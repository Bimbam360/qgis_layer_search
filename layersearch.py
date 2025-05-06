from qgis.PyQt.QtCore import Qt, QSettings, QObject, QItemSelectionModel
from qgis.PyQt.QtWidgets import (
    QLineEdit, QPushButton, QVBoxLayout, QWidget,
    QHBoxLayout, QDockWidget
)
from qgis.core import (
    QgsProject, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsMessageLog, Qgis
)
from qgis.gui import QgsLayerTreeView

class LayerSearchPlugin(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        QgsMessageLog.logMessage(
            "LayerSearch Plugin: Constructor called",
            'LayerSearch',
            level=Qgis.Info
        )
        # Load saved position if available
        self.settings = QSettings("QGIS", "LayerSearchPlugin")
        # Store original expanded groups per view
        self._original_expanded = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize UI components"""
        pass  # Setup done in initGui
    
    def initGui(self):
        QgsMessageLog.logMessage(
            "LayerSearch Plugin: Initializing GUI",
            'LayerSearch',
            level=Qgis.Info
        )
        self.searchWidget = QWidget()
        layout = QHBoxLayout(self.searchWidget)
        
        # Reduce layout margins and spacing
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        
        self.searchBox = QLineEdit()
        self.searchBox.setPlaceholderText("Search layers...")
        self.searchBox.textChanged.connect(self.on_search_text_changed)
        
        clearButton = QPushButton("Clear")
        clearButton.clicked.connect(self.clear_search)
        clearButton.setMaximumWidth(50)  # Make the button narrower
        
        layout.addWidget(self.searchBox)
        layout.addWidget(clearButton)
        
        for dock in self.iface.mainWindow().findChildren(QDockWidget):
            if "Layers" in dock.windowTitle():
                original = dock.widget()
                container = QWidget()
                vlay = QVBoxLayout(container)
                
                # Reduce vertical layout margins and spacing
                vlay.setContentsMargins(0, 0, 0, 0)
                vlay.setSpacing(0)
                
                vlay.addWidget(self.searchWidget)
                vlay.addWidget(original)
                vlay.setStretchFactor(self.searchWidget, 0)
                vlay.setStretchFactor(original, 1)
                dock.setWidget(container)
                break
    
    def find_matching_layers(self, node, search_text):
        """Recursively find all layers matching the search text starting from the given node"""
        matches = []
        
        # Check if this node is a layer
        if isinstance(node, QgsLayerTreeLayer):
            if search_text.lower() in node.layer().name().lower():
                matches.append(node)
        
        # Get all children of this node
        for child in node.children():
            # Recursively find matches in child nodes
            child_matches = self.find_matching_layers(child, search_text)
            matches.extend(child_matches)
        
        return matches
    
    def on_search_text_changed(self, text):
        """Handle search text changes"""
        QgsMessageLog.logMessage(
            f"LayerSearch Plugin: on_search_text_changed: '{text}'",
            'LayerSearch',
            level=Qgis.Info
        )
        
        root = QgsProject.instance().layerTreeRoot()
        
        for view in self.iface.mainWindow().findChildren(QgsLayerTreeView):
            # Save original expanded state if we haven't already
            if view not in self._original_expanded:
                self._original_expanded[view] = set()
                self.store_expanded_groups(root, view)
            
            # Clear current selection
            view.selectionModel().clearSelection()
            
            if not text:
                # Restore original expansion state when search is cleared
                self.restore_expansion_state(view, root)
                continue
                
            # Find all matching layers starting from root
            matches = self.find_matching_layers(root, text)
            
            # Determine groups to expand and those to keep expanded
            groups_to_expand = set()
            for node in matches:
                parent = node.parent()
                while parent and isinstance(parent, QgsLayerTreeGroup):
                    groups_to_expand.add(parent)
                    parent = parent.parent()
            
            # First handle all groups - expand if needed, collapse if shouldn't be expanded
            self.adjust_group_expansion(view, root, groups_to_expand)
            
            # Select all matching layers (equivalent to Ctrl+clicking each)
            for node in matches:
                idx = view.node2index(node)
                view.selectionModel().select(
                    idx,
                    QItemSelectionModel.Select | QItemSelectionModel.Rows
                )
            
            # Scroll to the first match if any
            if matches:
                idx = view.node2index(matches[0])
                view.scrollTo(idx)
    
    def store_expanded_groups(self, node, view):
        """Recursively store the expanded state of all groups"""
        if isinstance(node, QgsLayerTreeGroup):
            idx = view.node2index(node)
            if view.isExpanded(idx):
                self._original_expanded[view].add(node)
            
            # Check all children
            for child in node.children():
                if isinstance(child, QgsLayerTreeGroup):
                    self.store_expanded_groups(child, view)

    def adjust_group_expansion(self, view, node, groups_to_expand):
        """Recursively adjust expansion state of groups based on search results
        - Expand groups in groups_to_expand
        - Collapse groups that weren't originally expanded and aren't in groups_to_expand
        - Keep groups expanded if they were originally expanded
        """
        if isinstance(node, QgsLayerTreeGroup):
            idx = view.node2index(node)
            
            if node in groups_to_expand:
                # Group has matches, expand it
                view.expand(idx)
            elif node not in self._original_expanded[view]:
                # Group has no matches and wasn't originally expanded, collapse it
                view.collapse(idx)
                # No need to process children if collapsed
                return
            # else: Group was originally expanded, keep it expanded
            
            # Process children recursively
            for child in node.children():
                if isinstance(child, QgsLayerTreeGroup):
                    self.adjust_group_expansion(view, child, groups_to_expand)
                    
    
    def restore_expansion_state(self, view, node):
        """Recursively restore the expansion state of all groups"""
        if isinstance(node, QgsLayerTreeGroup):
            idx = view.node2index(node)
            if node in self._original_expanded[view]:
                view.expand(idx)
            else:
                view.collapse(idx)
            
            # Process all children
            for child in node.children():
                if isinstance(child, QgsLayerTreeGroup):
                    self.restore_expansion_state(view, child)
    
    def clear_search(self):
        """Clear search text and reset view"""
        QgsMessageLog.logMessage(
            "LayerSearch Plugin: clear_search called",
            'LayerSearch',
            level=Qgis.Info
        )
        self.searchBox.clear()
        root = QgsProject.instance().layerTreeRoot()
        
        for view in self.iface.mainWindow().findChildren(QgsLayerTreeView):
            view.selectionModel().clearSelection()
            if view in self._original_expanded:
                self.restore_expansion_state(view, root)
                del self._original_expanded[view]

def run_plugin(iface):
    return LayerSearchPlugin(iface)
