import re
from qgis.PyQt.QtCore import Qt, QSettings, QObject, QItemSelectionModel
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
	QLineEdit, QPushButton, QVBoxLayout, QWidget,
	QHBoxLayout, QDockWidget, QCheckBox, QColorDialog
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
			level=Qgis.MessageLevel.Info
		)
		self.settings = QSettings("QGIS", "LayerSearchPlugin")
		self._original_expanded = {}
		self._highlight_color = self.settings.value(
			"highlight_color", "#ffaa00"
		)

	def initGui(self):
		QgsMessageLog.logMessage(
			"LayerSearch Plugin: Initializing GUI",
			'LayerSearch',
			level=Qgis.MessageLevel.Info
		)
		self.searchWidget = QWidget()
		layout = QHBoxLayout(self.searchWidget)
		layout.setContentsMargins(2, 2, 2, 2)
		layout.setSpacing(4)

		self.searchBox = QLineEdit()
		self.searchBox.setPlaceholderText("Search layers...")
		self.searchBox.textChanged.connect(self.on_search_text_changed)

		self.clearButton = QPushButton("Clear")
		self.clearButton.clicked.connect(self.clear_search)
		self.clearButton.setMaximumWidth(50)

		self.regexToggle = QCheckBox("Regex")
		self.regexToggle.setChecked(False)
		self.regexToggle.toggled.connect(
			lambda: self.on_search_text_changed(self.searchBox.text())
		)

		self.colorButton = QPushButton()
		self.colorButton.setFixedSize(22, 22)
		self.colorButton.setToolTip("Pick highlight color")
		self.colorButton.clicked.connect(self.pick_color)
		self._update_color_button()

		layout.addWidget(self.searchBox)
		layout.addWidget(clearButton := self.clearButton)
		layout.addWidget(self.regexToggle)
		layout.addWidget(self.colorButton)

		for dock in self.iface.mainWindow().findChildren(QDockWidget):
			if "Layers" in dock.windowTitle():
				self._original_dock_widget = dock.widget()
				container = QWidget()
				vlay = QVBoxLayout(container)
				vlay.setContentsMargins(0, 0, 0, 0)
				vlay.setSpacing(0)
				vlay.addWidget(self.searchWidget)
				vlay.addWidget(self._original_dock_widget)
				vlay.setStretchFactor(self.searchWidget, 0)
				vlay.setStretchFactor(self._original_dock_widget, 1)
				dock.setWidget(container)
				break

	def _update_color_button(self):
		self.colorButton.setStyleSheet(
			f"background-color:{self._highlight_color}; border:1px solid #555;"
		)

	def pick_color(self):
		initial = QColor(self._highlight_color)
		color = QColorDialog.getColor(initial, None, "Pick highlight color")
		if color.isValid():
			self._highlight_color = color.name()
			self.settings.setValue("highlight_color", self._highlight_color)
			self._update_color_button()
			self.on_search_text_changed(self.searchBox.text())

	def _apply_highlight_stylesheet(self, view):
		view.setStyleSheet(
			f"QTreeView::item:selected {{ background: {self._highlight_color}; }}"
			f"QTreeView::item:selected:!active {{ background: {self._highlight_color}; }}"
		)

	def find_matching_layers(self, node, search_text):
		"""Recursively find all layers matching the search text starting from the given node."""
		matches = []
		if isinstance(node, QgsLayerTreeLayer):
			name = node.layer().name()
			if self.regexToggle.isChecked():
				try:
					if re.search(search_text, name):
						matches.append(node)
				except re.error:
					pass
			else:
				if search_text.lower() in name.lower():
					matches.append(node)
		for child in node.children():
			matches.extend(self.find_matching_layers(child, search_text))
		return matches

	def on_search_text_changed(self, text):
		"""Handle search text changes."""
		QgsMessageLog.logMessage(
			f"LayerSearch Plugin: on_search_text_changed: '{text}'",
			'LayerSearch',
			level=Qgis.MessageLevel.Info
		)
		root = QgsProject.instance().layerTreeRoot()
		for view in self.iface.mainWindow().findChildren(QgsLayerTreeView):
			view.selectionModel().clearSelection()

			if not text:
				view.setStyleSheet("")
				if view in self._original_expanded:
					self.restore_expansion_state(view, root)
					del self._original_expanded[view]
				continue

			self._apply_highlight_stylesheet(view)

			if view not in self._original_expanded:
				self._original_expanded[view] = set()
				self.store_expanded_groups(root, view)

			matches = self.find_matching_layers(root, text)

			groups_to_expand = set()
			for node in matches:
				parent = node.parent()
				while parent and isinstance(parent, QgsLayerTreeGroup):
					groups_to_expand.add(parent)
					parent = parent.parent()

			self.adjust_group_expansion(view, root, groups_to_expand)

			for node in matches:
				idx = view.node2index(node)
				view.selectionModel().select(
					idx,
					QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
				)

			if matches:
				idx = view.node2index(matches[0])
				view.scrollTo(idx)

	def store_expanded_groups(self, node, view):
		"""Recursively store the expanded state of all groups."""
		if isinstance(node, QgsLayerTreeGroup):
			idx = view.node2index(node)
			if view.isExpanded(idx):
				self._original_expanded[view].add(node)
			for child in node.children():
				if isinstance(child, QgsLayerTreeGroup):
					self.store_expanded_groups(child, view)

	def adjust_group_expansion(self, view, node, groups_to_expand):
		"""Recursively adjust expansion state of groups based on search results.

		Expands groups in groups_to_expand, collapses groups that were not
		originally expanded and are not in groups_to_expand, and preserves
		groups that were originally expanded.
		"""
		if not isinstance(node, QgsLayerTreeGroup):
			return
		root = QgsProject.instance().layerTreeRoot()
		if node is root:
			for child in node.children():
				if isinstance(child, QgsLayerTreeGroup):
					self.adjust_group_expansion(view, child, groups_to_expand)
			return
		idx = view.node2index(node)
		if node in groups_to_expand:
			view.expand(idx)
		elif node not in self._original_expanded.get(view, set()):
			view.collapse(idx)
			return
		for child in node.children():
			if isinstance(child, QgsLayerTreeGroup):
				self.adjust_group_expansion(view, child, groups_to_expand)

	def restore_expansion_state(self, view, node):
		"""Recursively restore the expansion state of all groups."""
		if not isinstance(node, QgsLayerTreeGroup):
			return
		root = QgsProject.instance().layerTreeRoot()
		if node is not root:
			idx = view.node2index(node)
			if node in self._original_expanded.get(view, set()):
				view.expand(idx)
			else:
				view.collapse(idx)
		for child in node.children():
			if isinstance(child, QgsLayerTreeGroup):
				self.restore_expansion_state(view, child)

	def clear_search(self):
		"""Clear search text and reset view."""
		QgsMessageLog.logMessage(
			"LayerSearch Plugin: clear_search called",
			'LayerSearch',
			level=Qgis.MessageLevel.Info
		)
		self.searchBox.clear()
		root = QgsProject.instance().layerTreeRoot()
		for view in self.iface.mainWindow().findChildren(QgsLayerTreeView):
			view.selectionModel().clearSelection()
			view.setStyleSheet("")
			if view in self._original_expanded:
				self.restore_expansion_state(view, root)
				del self._original_expanded[view]

	def unload(self):
		"""Restore original Layers dock and disconnect signals."""
		for dock in self.iface.mainWindow().findChildren(QDockWidget):
			if "Layers" in dock.windowTitle():
				if hasattr(self, '_original_dock_widget') and self._original_dock_widget:
					dock.setWidget(self._original_dock_widget)

				if hasattr(self, 'searchBox') and self.searchBox:
					try:
						self.searchBox.textChanged.disconnect(self.on_search_text_changed)
					except TypeError:
						pass

				if hasattr(self, 'clearButton') and self.clearButton:
					try:
						self.clearButton.clicked.disconnect(self.clear_search)
					except TypeError:
						pass

				if hasattr(self, 'colorButton') and self.colorButton:
					try:
						self.colorButton.clicked.disconnect(self.pick_color)
					except TypeError:
						pass

				break

		for view in self.iface.mainWindow().findChildren(QgsLayerTreeView):
			view.setStyleSheet("")

		self._original_expanded = {}
		self.searchWidget = None
		self.searchBox = None
		self.clearButton = None
		self.colorButton = None


def run_plugin(iface):
	return LayerSearchPlugin(iface)