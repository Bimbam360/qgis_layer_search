# 🔍 LayerSearch Plugin for QGIS

## 📄 Overview
**LayerSearch** — Ever have a project with tens or even hundreds of layers nested in various Groups and found it a PITA to find the layer you want? Same.
![Layer Search](https://github.com/user-attachments/assets/b42ca30f-5682-41cd-bfdc-fdb8f47a2f6d)

## ✨ Features
- Adds a simple search box to the Layers panel.
- Filters layers based on substring matches (case-insensitive).
- Automatically expands groups containing matching layers.
- Restores original group expansion state when the search is cleared.
- Highlights matching layers in the Layers panel.

## 🧭 Usage
1. Install and enable the plugin through the QGIS Plugin Manager.
2. A search bar will appear at the top of the Layers panel.
3. Start typing any part of a layer's name.
4. Matching layers will be highlighted and their parent groups expanded.
5. Click "Clear" or delete the search string to reset the panel to its original state.

## ⚙️ Implementation Notes
- Search is applied recursively on the layer tree.
- Only the layer names are considered for matching.
- Expansion state is preserved per view and restored when the search is cleared.

## 🛠️ Development
- [x] Basic Search  
- [ ] Fuzzy Match Search / options

## 📜 License
MIT License (or specify applicable license)

## 👤 Author
Beau Seymour
