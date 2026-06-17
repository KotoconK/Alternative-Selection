import maya.cmds as cmds
import maya.mel as mel


WINDOW_NAME = "faceEdgeEveryNWindow"


def get_selected_faces_in_order():
    cmds.selectPref(trackSelectionOrder=True)

    faces = cmds.ls(orderedSelection=True, flatten=True) or []
    if not faces:
        faces = cmds.ls(selection=True, flatten=True) or []

    return faces


def get_face_neighbors(face):
    edges = cmds.polyListComponentConversion(face, fromFace=True, toEdge=True)
    edges = cmds.ls(edges, flatten=True) or []

    neighbors = set()

    for edge in edges:
        connected_faces = cmds.polyListComponentConversion(edge, fromEdge=True, toFace=True)
        connected_faces = cmds.ls(connected_faces, flatten=True) or []

        for f in connected_faces:
            if f != face:
                neighbors.add(f)

    return neighbors


def validate_face_loop(faces):
    if not faces:
        return False, "No faces selected."

    if not all(".f[" in f for f in faces):
        return False, "Please select faces only."

    objects = list(set(f.split(".")[0] for f in faces))
    if len(objects) != 1:
        return False, "Please select faces from a single object."

    selected_set = set(faces)

    adjacency = {}
    for face in faces:
        neighbors = get_face_neighbors(face)
        selected_neighbors = neighbors.intersection(selected_set)
        adjacency[face] = selected_neighbors

    neighbor_counts = [len(adjacency[f]) for f in faces]

    if any(count == 0 or count > 2 for count in neighbor_counts):
        return False, "The selection does not look like a valid face loop."

    ones = neighbor_counts.count(1)
    twos = neighbor_counts.count(2)

    valid_closed_loop = twos == len(faces)
    valid_open_loop = ones == 2 and (ones + twos) == len(faces)

    if not (valid_closed_loop or valid_open_loop):
        return False, "The selection does not look like a continuous face loop."

    visited = set()
    to_visit = [faces[0]]

    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        visited.add(current)
        to_visit.extend(adjacency[current] - visited)

    if visited != selected_set:
        return False, "The selected faces do not form one connected loop."

    return True, "OK"


def select_every_n_faces(*args):
    step = cmds.intSliderGrp("faceEveryNStepSlider", query=True, value=True)
    offset = cmds.intSliderGrp("faceEveryNOffsetSlider", query=True, value=True)

    faces = get_selected_faces_in_order()

    is_valid, message = validate_face_loop(faces)
    if not is_valid:
        cmds.warning(message)
        cmds.confirmDialog(
            title="Invalid Selection",
            message=message,
            button=["OK"],
            defaultButton="OK"
        )
        return

    result = faces[offset::step]

    if not result:
        cmds.warning("No faces were selected with the current values.")
        return

    cmds.select(result, replace=True)


def select_every_n_edges(*args):
    step = cmds.intSliderGrp("edgeEveryNStepSlider", query=True, value=True)

    sel = cmds.ls(selection=True, flatten=True) or []
    if not sel:
        cmds.warning("No selection found.")
        return

    if not all(".e[" in s for s in sel):
        cmds.warning("Please select edges to use this option.")
        cmds.confirmDialog(
            title="Invalid Selection",
            message="Please select edges to use this option.",
            button=["OK"],
            defaultButton="OK"
        )
        return

    mel.eval('polySelectEdgesEveryN "edgeRing" %d;' % step)
    
def select_every_n_vertices(*args):
    step = cmds.intSliderGrp("vertexEveryNStepSlider", query=True, value=True)
    offset = cmds.intSliderGrp("vertexEveryNOffsetSlider", query=True, value=True)

    cmds.selectPref(trackSelectionOrder=True)
    verts = cmds.ls(orderedSelection=True, flatten=True) or []
    if not verts:
        cmds.warning("No selection found.")
        return

    if not all(".vtx[" in v for v in verts):
        cmds.warning("Please select vertices only.")
        cmds.confirmDialog(
            title="Invalid Selection",
            message="Please select vertices only.",
            button=["OK"],
            defaultButton="OK"
        )
        return

    result = verts[offset::step]

    if not result:
        cmds.warning("No vertices were selected with the current values.")
        return

    cmds.select(result, replace=True)

def build_ui():
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME)

    cmds.window(
        WINDOW_NAME,
        title="Select Every N Components",
        sizeable=False
    )

    main_layout = cmds.columnLayout(
        adjustableColumn=True,
        rowSpacing=10
    )

    # Faces
    cmds.frameLayout(
        label="Faces",
        collapsable=False,
        marginWidth=14,
        marginHeight=14,
        parent=main_layout
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=8)

    cmds.text(label="Select a face loop first, then apply the pattern.", align="left")

    cmds.intSliderGrp(
        "faceEveryNStepSlider",
        label="Every how many faces",
        field=True,
        minValue=1,
        maxValue=20,
        value=2,
        columnWidth=[(1, 140), (2, 50), (3, 220)]
    )

    cmds.intSliderGrp(
        "faceEveryNOffsetSlider",
        label="Offset / start",
        field=True,
        minValue=0,
        maxValue=20,
        value=0,
        columnWidth=[(1, 140), (2, 50), (3, 220)]
    )

    cmds.button(label="Select Faces", height=34, command=select_every_n_faces)

    cmds.setParent("..")
    cmds.setParent("..")

    # Edges
    cmds.frameLayout(
        label="Edges",
        collapsable=False,
        marginWidth=14,
        marginHeight=14,
        parent=main_layout
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6)

    cmds.text(label='Uses polySelectEdgesEveryN with "edgeRing" mode.', align="left")

    cmds.intSliderGrp(
        "edgeEveryNStepSlider",
        label="Every how many edges",
        field=True,
        minValue=1,
        maxValue=20,
        value=2,
        columnWidth=[(1, 140), (2, 50), (3, 220)]
    )

    cmds.button(label="Select Edges", height=34, command=select_every_n_edges)

    cmds.setParent("..")
    cmds.setParent("..")

    # Vertices
    cmds.frameLayout(
        label="Vertices",
        collapsable=False,
        marginWidth=14,
        marginHeight=14,
        parent=main_layout
    )

    cmds.columnLayout(adjustableColumn=True, rowSpacing=8)

    cmds.text(
        label="Uses the current vertex selection order.",
        align="left"
    )

    cmds.intSliderGrp(
        "vertexEveryNStepSlider",
        label="Every how many vertices",
        field=True,
        minValue=1,
        maxValue=20,
        value=2,
        columnWidth=[(1, 140), (2, 50), (3, 220)]
    )

    cmds.intSliderGrp(
        "vertexEveryNOffsetSlider",
        label="Offset / start",
        field=True,
        minValue=0,
        maxValue=20,
        value=0,
        columnWidth=[(1, 140), (2, 50), (3, 220)]
    )

    cmds.button(
        label="Select Vertices",
        height=34,
        command=select_every_n_vertices
    )

    cmds.setParent("..")
    cmds.setParent("..")

    cmds.separator(height=4, style="none")  
    cmds.text(label="Developed by Álvaro_A", align="center")
    cmds.separator(height=8, style="none")  

    cmds.showWindow(WINDOW_NAME)


build_ui()
