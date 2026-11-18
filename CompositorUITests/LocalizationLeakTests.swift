import XCTest

/// Fails when the Chinese UI shows English.
///
/// The static audits (`audit_strings.py`, `audit_keys.py`) catch a literal with no catalog entry,
/// but they cannot see the fourth leak class: text that is English on screen even though the
/// catalog is fine — a string built at runtime, an AppKit title set from a raw value, a label that
/// only localizes in one code path. This test is the runtime counterpart: it launches the app
/// under zh-Hans and reads the labels the accessibility layer actually exposes.
///
/// What counts as a leak: a label made only of printable ASCII that contains a run of at least
/// three letters. Pure punctuation, numbers, units, and single-letter identifiers are left alone —
/// they are not English words. `tools/localization/ui-allowlist.txt` exempts the values which
/// standards §4.5 says must stay English (ColorSync profile names, format acronyms, the letter T).
///
/// A found leak names the screen and the label, so the fix is obvious without re-running.
final class LocalizationLeakTests: XCTestCase {
    /// Labels collected from every screen visited, with the screen they came from.
    private var leaks: [(screen: String, label: String)] = []

    @MainActor
    func testChineseInterfaceHasNoEnglish() throws {
        let app = XCUIApplication()
        app.launchArguments = [
            "-ApplePersistenceIgnoreState", "YES", "-SUEnableAutomaticChecks", "NO",
            "-AppleLanguages", "(zh-Hans)", "-AppleLocale", "zh_CN",
        ]
        app.launch()

        let window = app.windows.firstMatch
        XCTAssertTrue(window.waitForExistence(timeout: 20), "the editor window")
        Thread.sleep(forTimeInterval: 2)

        inspect("Start", in: app)

        // The menu bar is where English leaks most often: AppKit titles come from raw values and
        // are not covered by the SwiftUI catalog lookup.
        //
        // One scan, not one per menu. AppKit puts the whole menu tree — every item of every menu —
        // in the accessibility snapshot at once (the first run enumerated to index 257 across nine
        // menus, which is ~28 items each: they cannot have come from one open menu). Each
        // allElementsBoundByIndex call is a fresh snapshot costing ~0.3s per element, so scanning
        // three element types per menu took 835s; once is 90s at worst and covers the same tree.
        let menus = app.menuBars.menuBarItems
        for index in 0..<menus.count {
            let title = menus.element(boundBy: index).label
            if isLeak(title) { leaks.append((screen: "menu bar", label: title)) }
        }

        // Opening one menu materializes the tree in the snapshot; the scan then reads all of it.
        if menus.count > 0 {
            menus.element(boundBy: 0).click()
            Thread.sleep(forTimeInterval: 0.8)
            inspect("menus", in: app)
        }

        // The sheets most likely to show untranslated text, by their own shortcuts.
        for (name, key, extra) in [("Image Size", "i", XCUIElement.KeyModifierFlags([.command, .option])),
                                   ("Hue Saturation", "u", XCUIElement.KeyModifierFlags.command)] {
            app.typeKey(key, modifierFlags: extra)
            Thread.sleep(forTimeInterval: 1.5)
            inspect(name, in: app)
            app.typeKey(.escape, modifierFlags: [])
            Thread.sleep(forTimeInterval: 0.5)
        }

        report()
    }

    /// Collects the labels of the elements on screen, recording the ones that look like English.
    ///
    /// Menu items are included: with a menu open, `app.menuItems` returns the whole menu tree, so
    /// one call here covers every menu rather than only the open one.
    @MainActor
    private func inspect(_ screen: String, in app: XCUIApplication) {
        for element in app.staticTexts.allElementsBoundByIndex {
            let label = element.label
            if isLeak(label) { leaks.append((screen: screen, label: label)) }
        }
        for element in app.buttons.allElementsBoundByIndex {
            let label = element.label
            if isLeak(label) { leaks.append((screen: screen, label: label)) }
        }
        for element in app.menuItems.allElementsBoundByIndex {
            let label = element.label
            if isLeak(label) { leaks.append((screen: screen, label: label)) }
        }
    }

    /// Whether a label is English that should have been Chinese.
    private func isLeak(_ label: String) -> Bool {
        let text = label.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return false }

        // Translated means it contains a CJK character. Merely being non-ASCII is not enough:
        // "New canvas (⌘N)" and "1920 × 1080" are English labels with symbols in them, and must
        // be caught rather than waved through.
        guard text.range(of: cjkPattern, options: .regularExpression) == nil else { return false }

        // A run of three or more letters. Shorter than that and it is an identifier, a unit, or a
        // keyboard hint (T, px, ⌘) rather than a word.
        guard text.range(of: "[A-Za-z]{3,}", options: .regularExpression) != nil else { return false }

        // Exempt the values the standards say must stay English. Matched as whole words: a bare
        // "T" must not exempt every label containing a t, which would pass "Filter" and "Undo".
        for allowed in allowlist {
            let pattern = "(?<![A-Za-z0-9])" + NSRegularExpression.escapedPattern(for: allowed)
                + "(?![A-Za-z0-9])"
            let range = NSRange(text.startIndex..., in: text)
            if (try? NSRegularExpression(pattern: pattern, options: [.caseInsensitive])
                .firstMatch(in: text, range: range)) != nil {
                return false
            }
        }
        return true
    }

    /// The scripts that mean a label was translated. Merely being non-ASCII does not: key symbols
    /// and the multiplication sign appear in English labels.
    private let cjkPattern = "[\u{3000}-\u{303F}\u{3040}-\u{30FF}\u{3400}-\u{4DBF}"
        + "\u{4E00}-\u{9FFF}\u{F900}-\u{FAFF}\u{FF00}-\u{FFEF}]"

    private func report() {
        guard !leaks.isEmpty else { return }

        // Deduplicated, since the same label shows up on several screens.
        var seen: Set<String> = []
        var lines: [String] = []
        for leak in leaks where seen.insert("\(leak.screen)|\(leak.label)").inserted {
            lines.append("  \(leak.screen): \"\(leak.label)\"")
        }

        XCTFail("""
            \(lines.count) English label(s) in the zh-Hans interface.
            Either translate them, or — if standards §4.5 says they are data rather than words —
            add them to tools/localization/ui-allowlist.txt with the reason:

            \(lines.joined(separator: "\n"))
            """)
    }

    /// The exempted English, from tools/localization/ui-allowlist.txt.
    ///
    /// `#filePath` is this source file's path as the compiler saw it, which is inside the checkout
    /// on the machine running the tests, so the list is read from the repository rather than from
    /// the built bundle.
    private lazy var allowlist: [String] = {
        let url = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()      // CompositorUITests
            .deletingLastPathComponent()      // repository root
            .appendingPathComponent("tools/localization/ui-allowlist.txt")
        guard let text = try? String(contentsOf: url, encoding: .utf8) else {
            XCTFail("cannot read \(url.path) — the allowlist must be in the checkout")
            return []
        }
        return text.split(separator: "\n")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty && !$0.hasPrefix("#") }
    }()
}
