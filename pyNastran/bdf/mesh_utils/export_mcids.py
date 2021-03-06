"""
Defines:
 - nodes, bars = export_mcids(bdf_filename, csv_filename=None)
"""
from __future__ import print_function
from six import integer_types, string_types, iteritems
import numpy as np
from pyNastran.bdf.bdf import read_bdf


def export_mcids(bdf_filename, csv_filename=None,
                 eids=None, export_xaxis=True, export_yaxis=True,
                 iply=0):
    """
    Exports the element material coordinates systems, so you can
    load it into pyNastranGUI.

    Parameters
    ----------
    bdf_filename : str/BDF
        a bdf filename or BDF model
    csv_filename : str; default=None
        the path to the output csv
    eids : List[int]
        the element ids to consider
    export_xaxis : bool; default=True
        export the x-axis
    export_yaxis : bool; default=True
        export the x-axis
    iply : int; default=0
        TDOO: not validated
        the ply to consider

        PSHELL
        ======
        iply   location
        ----   --------
         0      mid1 or mid2
         1      mid1
         2      mid2
         3      mid3
         4      mid4

        PCOMP/PCOMPG
        ============
        iply   location
        ----   --------
        0      layer1
        1      layer2


    Returns
    -------
    nodes : (nnodes, 3) float list
        the nodes
    bars : (nbars, 2) int list
    """
    if isinstance(bdf_filename, string_types):
        model = read_bdf(bdf_filename, xref=False)
        #print(model.get_bdf_stats())
        model.safe_cross_reference()
    else:
        model = bdf_filename

    skip_types = [
        'CELAS1', 'CELAS2', 'CELAS3', 'CELAS4', 'CELAS5',
        'CDAMP1', 'CDAMP2', 'CDAMP3', 'CDAMP4',
        'CBUSH', 'CBUSH1D', 'CBUSH2D', 'CGAP',
        'CROD', 'CONROD',
        'CBAR', 'CBEAM',
        'CTETRA', 'CPYRAM', 'CPENTA', 'CHEXA',
        'CRAC2D', 'CRAC3D',
    ]

    eid = 1
    nid = 1
    nodes = []
    bars = []
    consider_property_rotation = True  # not tested
    export_both_axes = export_xaxis and export_yaxis
    assert export_xaxis or export_yaxis

    if eids is None:
        elements = model.elements
    else:
        elements = {eid : model.elements[eid] for eid in eids}

    pids_failed = set([])
    for eidi, elem in sorted(iteritems(elements)):
        if elem.type in ['CQUAD4', 'CQUAD8', 'CQUAD']:
            pid_ref = elem.pid_ref
            if pid_ref.type == 'PSHELL':
                mid = pid_ref.mid1_ref
                if mid.type in ['MAT1']:
                    continue
                elif mid.type in ['MAT8']:
                    pass
                else:
                    raise NotImplementedError(pid_ref)
            elif pid_ref.type in ['PCOMP', 'PCOMPG']:
                pass
            else:
                raise NotImplementedError(pid_ref)
            xyz1 = elem.nodes_ref[0].get_position()
            xyz2 = elem.nodes_ref[1].get_position()
            xyz3 = elem.nodes_ref[2].get_position()
            xyz4 = elem.nodes_ref[3].get_position()

            dxyz21 = np.linalg.norm(xyz2 - xyz1)
            dxyz32 = np.linalg.norm(xyz3 - xyz2)
            dxyz43 = np.linalg.norm(xyz4 - xyz3)
            dxyz14 = np.linalg.norm(xyz1 - xyz4)
            dxyz = np.mean([dxyz21, dxyz32, dxyz43, dxyz14]) / 2.
            centroid, imat, jmat, normal = elem.material_coordinate_system()

            try:
                imat, jmat = _rotate_mcid(
                    elem, pid_ref, iply, imat, jmat, normal,
                    consider_property_rotation=consider_property_rotation)
            except IndexError:
                pids_failed.add(pid_ref.pid)
                continue

            iaxis = centroid + imat * dxyz
            jaxis = centroid + jmat * dxyz
            nid, eid = _add_elements(nid, eid, nodes, bars,
                                     centroid, iaxis, jaxis,
                                     export_both_axes, export_xaxis)

        elif elem.type in ['CTRIA3']:
            pid_ref = elem.pid_ref
            if pid_ref.type == 'PSHELL':
                mid = pid_ref.mid1_ref
                if mid.type in ['MAT1']:
                    continue
                elif mid.type in ['MAT8']:
                    pass
                else:
                    raise NotImplementedError(pid_ref)
            elif pid_ref.type in ['PCOMP', 'PCOMPG']:
                pass
            else:
                raise NotImplementedError(pid_ref)

            xyz1 = elem.nodes_ref[0].get_position()
            xyz2 = elem.nodes_ref[1].get_position()
            xyz3 = elem.nodes_ref[2].get_position()

            dxyz21 = np.linalg.norm(xyz2 - xyz1)
            dxyz32 = np.linalg.norm(xyz3 - xyz2)
            dxyz13 = np.linalg.norm(xyz1 - xyz3)
            dxyz = np.mean([dxyz21, dxyz32, dxyz13]) / 2.
            centroid, imat, jmat, normal = elem.material_coordinate_system()

            try:
                imat, jmat = _rotate_mcid(
                    elem, pid_ref, iply, imat, jmat, normal,
                    consider_property_rotation=consider_property_rotation)
            except IndexError:
                pids_failed.add(pid_ref.pid)
                continue

            iaxis = centroid + imat * dxyz
            jaxis = centroid + jmat * dxyz
            nid, eid = _add_elements(nid, eid, nodes, bars,
                                     centroid, iaxis, jaxis,
                                     export_both_axes, export_xaxis)
        elif elem.type in skip_types:
            pass
        else:
            msg = 'element type=%r is not supported\n%s' % (elem.type, elem)
            raise NotImplementedError(msg)

    if len(nodes) == 0:
        msg = 'No material coordinate systems could be found\n'
        pids_failed_list = list(pids_failed)
        pids_failed_list.sort()
        pid_str = [str(pid) for pid in pids_failed_list]
        msg += 'iPly=%r; Property IDs failed: [%s]\n' % (iply, ', '.join(pid_str))

        for pid in pids_failed_list:
            prop = model.properties[pid]
            msg += 'Property %s:\n%s\n' % (pid, prop)
        raise RuntimeError(msg)
    if csv_filename:
        with open(csv_filename, 'w') as out_file:
            for node in nodes:
                out_file.write('GRID,%i,%s,%s,%s\n' % node)
            for bari in bars:
                out_file.write('BAR,%i,%i,%i\n' % bari)
    return nodes, bars

def _rotate_mcid(elem, pid_ref, iply, imat, jmat, normal,
                 consider_property_rotation=True):
    """rotates a material coordinate system"""
    if consider_property_rotation:
        pid_ref = elem.pid_ref
        if pid_ref.type == 'PSHELL':
            theta_mcid = elem.theta_mcid
            if isinstance(theta_mcid, float):
                thetad = theta_mcid
            elif isinstance(theta_mcid, integer_types):
                return imat, jmat
            else:
                msg = 'theta/mcid=%r is not an int/float; type=%s\n%s' % (
                    theta_mcid, type(theta_mcid), elem)
                raise TypeError(msg)
        elif pid_ref.type in ['PCOMP', 'PCOMPG']:
            #print(pid_ref.nplies)
            thetad = pid_ref.get_theta(iply)
        else:
            msg = 'property type=%r is not supported\n%s%s' % (
                elem.pid_ref.type, elem, elem.pid_ref)
            raise NotImplementedError(msg)
        if thetad == 0.0:  # catches on mcid=0 as well
            return imat, jmat

        theta = np.radians(thetad)
        c = np.cos(theta)
        s = np.sin(theta)

        R = np.array([
            [c, -s, 0.],
            [s, c, 0.],
            [0., 0., 1.]
            ], dtype='float64')

        R1 = np.vstack([imat, jmat, normal])
        R2 = np.dot(R, R1)  ## TODO: validate
        imat2 = R2[0, :]
        jmat2 = R2[1, :]
        return imat2, jmat2

def _add_elements(nid, eid, nodes, bars,
                  centroid, iaxis, jaxis,
                  export_both_axes, export_xaxis):
    """adds the element data"""
    if export_both_axes:
        nodes.append((nid, centroid[0], centroid[1], centroid[2]))
        nodes.append((nid + 1, iaxis[0], iaxis[1], iaxis[2]))
        nodes.append((nid + 2, jaxis[0], jaxis[1], jaxis[2]))
        bars.append((eid, nid, nid + 1))  # x-axis
        bars.append((eid + 1, nid, nid + 2))  # y-axis
        nid += 3
        eid += 2
    elif export_xaxis:
        nodes.append((nid, centroid[0], centroid[1], centroid[2]))
        nodes.append((nid + 1, iaxis[0], iaxis[1], iaxis[2]))
        bars.append((eid, nid, nid + 1))  # x-axis
        nid += 2
        eid += 1
    else:
        # export_yaxis
        nodes.append((nid, centroid[0], centroid[1], centroid[2]))
        nodes.append((nid + 1, jaxis[0], jaxis[1], jaxis[2]))
        bars.append((eid, nid, nid + 1))  # y-axis
        nid += 2
        eid += 1
    return nid, eid
