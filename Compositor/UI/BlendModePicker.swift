import SwiftUI
import AppKit

struct BlendModePicker: NSViewRepresentable {
    let session: EditorSession

    func makeCoordinator() -> Coordinator {
        Coordinator(session: session)
    }

    func makeNSView(context: Context) -> NSPopUpButton {
        let button = NSPopUpButton(frame: .zero, pullsDown: false)

        // 按 Photoshop 的分组显示，同时保留每个模式真实枚举索引，
        // 这样显示中文后仍能正确识别对应的混合模式。
        for (groupIndex, group) in LayerBlendMode.groups.enumerated() {
            if groupIndex > 0 {
                button.menu?.addItem(.separator())
            }

            for mode in group {
                button.addItem(withTitle: mode.localizedName)

                if let item = button.lastItem,
                   let index = LayerBlendMode.allCases.firstIndex(of: mode) {
                    item.tag = index
                }
            }
        }

        button.menu?.delegate = context.coordinator
        button.target = context.coordinator
        button.action = #selector(Coordinator.choose(_:))

        button.setAccessibilityLabel(localizedString("Blend mode"))

        // 与 SwiftUI 其他胶囊按钮保持一致。
        button.borderShape = .capsule

        return button
    }
    /// As wide as it's offered. Left to itself, the pop-up insists on the width of its longest mode, wider than a
    /// narrow Layers panel has room for, and that pushed the whole panel out past its edges.
    func sizeThatFits(_ proposal: ProposedViewSize, nsView button: NSPopUpButton, context: Context) -> CGSize? {
        let natural = button.intrinsicContentSize
        guard let width = proposal.width, width.isFinite else { return natural }
        return CGSize(width: max(width, 60), height: natural.height)
    }
    func updateNSView(_ button: NSPopUpButton, context: Context) {
        button.isEnabled = session.canEditAppearance

        if !context.coordinator.tracking {
            let mode = session.activeLayer?.blendMode ?? .normal

            if let index = LayerBlendMode.allCases.firstIndex(of: mode) {
                let menuIndex = button.indexOfItem(withTag: index)

                if menuIndex >= 0 {
                    button.selectItem(at: menuIndex)
                }
            }
        }
    }

    static func dismantleNSView(
        _ button: NSPopUpButton,
        coordinator: Coordinator
    ) {
        if coordinator.tracking {
            coordinator.session.previewBlendMode(nil, for: nil)
        }

        button.menu?.delegate = nil
    }

    final class Coordinator: NSObject, NSMenuDelegate {
        let session: EditorSession

        var tracking = false

        private var layerID: UUID?
        private var highlightedMode: LayerBlendMode?

        init(session: EditorSession) {
            self.session = session
        }

        func menuWillOpen(_ menu: NSMenu) {
            tracking = true
            layerID = session.activeLayerID
            highlightedMode = nil
        }

        func menu(_ menu: NSMenu, willHighlight item: NSMenuItem?) {
            guard let item,
                  !item.isSeparatorItem,
                  LayerBlendMode.allCases.indices.contains(item.tag)
            else {
                return
            }

            let mode = LayerBlendMode.allCases[item.tag]

            highlightedMode = mode
            session.previewBlendMode(mode, for: layerID)
        }

        func menuDidClose(_ menu: NSMenu) {
            tracking = false

            DispatchQueue.main.async { [weak self] in
                guard let self, !self.tracking else {
                    return
                }

                self.session.previewBlendMode(nil, for: nil)
            }
        }

        @objc func choose(_ button: NSPopUpButton) {
            let selectedMode: LayerBlendMode?

            if let highlightedMode {
                selectedMode = highlightedMode
            } else if let item = button.selectedItem,
                      !item.isSeparatorItem,
                      LayerBlendMode.allCases.indices.contains(item.tag) {
                selectedMode = LayerBlendMode.allCases[item.tag]
            } else {
                selectedMode = nil
            }

            guard session.activeLayerID == layerID,
                  let mode = selectedMode
            else {
                return
            }

            session.setLayerBlendMode(mode)

            if let index = LayerBlendMode.allCases.firstIndex(of: mode) {
                let menuIndex = button.indexOfItem(withTag: index)

                if menuIndex >= 0 {
                    button.selectItem(at: menuIndex)
                }
            }

            highlightedMode = nil
            session.refreshCanvasPreview?()
        }
    }
}
