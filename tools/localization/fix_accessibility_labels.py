#!/usr/bin/env python3
import json
import re

project_path = "/Users/yi/Desktop/Compositor-CN"

print("步骤 1：添加 'Linked' 词条到 Localizable.xcstrings")
xcstrings_path = f"{project_path}/Compositor/Localizable.xcstrings"

with open(xcstrings_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_text = '''    "Folder": {
      "localizations": {
        "zh-Hans": {
          "stringUnit": {
            "state": "translated",
            "value": "文件夹"
          }
        }
      }
    },
    "Missing source": {'''

new_text = '''    "Folder": {
      "localizations": {
        "zh-Hans": {
          "stringUnit": {
            "state": "translated",
            "value": "文件夹"
          }
        }
      }
    },
    "Linked": {
      "localizations": {
        "zh-Hans": {
          "stringUnit": {
            "state": "translated",
            "value": "已链接"
          }
        }
      }
    },
    "Missing source": {'''

if old_text in content:
    new_content = content.replace(old_text, new_text, 1)
    with open(xcstrings_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✓ 成功添加 'Linked' 词条")
else:
    print("✗ 未找到插入位置")

print("\n步骤 2：修改 NativeLayerList.swift 使用 localizedString()")
swift_path = f"{project_path}/Compositor/UI/NativeLayerList.swift"

with open(swift_path, 'r', encoding='utf-8') as f:
    swift_content = f.read()

swift_content = swift_content.replace(
    'NSImage(systemSymbolName: "link", accessibilityDescription: "Linked")',
    'NSImage(systemSymbolName: "link", accessibilityDescription: localizedString("Linked"))'
)

swift_content = swift_content.replace(
    'NSImage(systemSymbolName: "folder", accessibilityDescription: "Folder")',
    'NSImage(systemSymbolName: "folder", accessibilityDescription: localizedString("Folder"))'
)

swift_content = swift_content.replace(
    'icon.accessibilityDescription = "Folder"',
    'icon.accessibilityDescription = localizedString("Folder")'
)

with open(swift_path, 'w', encoding='utf-8') as f:
    f.write(swift_content)

print("✓ 成功修改 NativeLayerList.swift")
print("\n修改完成！")
