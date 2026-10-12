import AppKit
import Testing
@testable import Compositor

/// The snap hook runs in AppKit before a native slider cell starts tracking a track press.
@MainActor
@Suite(.serialized)
struct SliderSnapTests {
    @Test func clickingTheTrackSnapsBeforeNativeTrackingBegins() async throws {
        SliderSnap.install()
        let window = NSWindow(contentRect: CGRect(x: 200, y: 200, width: 260, height: 50), styleMask: [.titled],
                              backing: .buffered, defer: false)
        let slider = NSSlider(value: 0.1, minValue: 0, maxValue: 1, target: nil, action: nil)
        slider.frame = CGRect(x: 20, y: 10, width: 220, height: 30)
        window.contentView?.addSubview(slider)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        // A slider cell learns its track's rectangle only when it draws, and the macOS 27 SDK no longer draws
        // a window as it's ordered front, so draw it before pressing as a person would always see it first.
        window.displayIfNeeded()
        defer { window.orderOut(nil) }
        let cell = try #require(slider.cell as? NSSliderCell)
        let press = NSPoint(x: slider.bounds.width * 0.9, y: slider.bounds.midY)
        // The cell reports no geometry until the slider has been laid out and drawn: read too early and the knob
        // measures as wide as the track, leaving nothing to work the expected value out from. Wait for real
        // geometry instead of guessing how long that takes.
        var knob = CGRect.zero, track = slider.bounds
        for _ in 0..<40 {
            window.contentView?.layoutSubtreeIfNeeded()
            knob = cell.knobRect(flipped: slider.isFlipped)
            track = cell.trackRect.isEmpty ? slider.bounds : cell.trackRect
            if track.width > knob.width { break }
            try await Task.sleep(for: .milliseconds(50))
        }
        // Where a click should land follows from the knob the system draws: its center can travel only between half
        // its width from either end of the track. Upstream's 0.94 was that sum written down for the 20-point knob of
        // an older macOS, and it stopped holding when the system changed how it draws a slider. Work the value out
        // from the cell instead, so the test keeps meaning whatever the knob measures.
        let travel = track.width - knob.width
        #expect(travel > 0, "the slider draws a track longer than its knob")
        let expected = min(1.0, max(0.0, Double((press.x - track.minX - knob.width / 2) / travel)))
        _ = cell.startTracking(at: press, in: slider)
        #expect(abs(slider.doubleValue - expected) < 0.02,
                "value should snap under the click before tracking: \(slider.doubleValue), expected \(expected)")
        // Only the geometry above is worked out, so also check the snap really moved the value to the click.
        #expect(abs(slider.doubleValue - 0.1) > 0.5, "the value jumped to the click: \(slider.doubleValue)")
    }
}
