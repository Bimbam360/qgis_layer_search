# <img src="https://github.com/user-attachments/assets/45b50592-1053-4582-b9f9-45af2a5b546d" alt="Icon" width="64" height="64" /> QGIS Layer Search Plugin

## Overview
Ever have a project with tens or even hundreds of layers nested in various Groups and found it a PITA to find the layer you want? Same!
So I developed Layer Search, a simple plugin that adds search functionality to the Layers panel:

![Layer Search](https://github.com/user-attachments/assets/b42ca30f-5682-41cd-bfdc-fdb8f47a2f6d)

## Usage
1. Install and enable the plugin through the QGIS Plugin Manager (TBD - For the time being copy to your plugin directory and enable manually).
2. A search bar will appear at the top of the Layers panel.
3. Start typing any part of a layer's name.
4. Matching layers will be highlighted and their parent groups expanded.
5. Click "Clear" or delete the search string to reset the panel to its original state.

## Implementation Notes
- Search is applied recursively on the layer tree.
- Only the layer names are considered for matching.
- Expansion state is preserved per view and restored when the search is cleared.

## Development
- [x] Basic Search  
- [ ] Fuzzy Match Search / options? Not sure if necessary tbh

## License
MIT License

## Author
Beau Seymour
