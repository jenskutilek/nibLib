#MenuTitle: Add Nib Guide Layer from Current Background
import copy

mid = Layer.master.id
n = GSLayer()
n.name = "nib"
n.width = Layer.width
n.associatedMasterId = mid
n.shapes = copy.copy(Layer.background.shapes)
Layer.parent.layers.append(n)

Layer.background.clear()
