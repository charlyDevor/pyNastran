# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from six import iteritems

from PyQt4 import QtCore, QtGui
from numpy import setdiff1d, unique, array, hstack

from pyNastran.bdf.utils import parse_patran_syntax, parse_patran_syntax_dict
from pyNastran.bdf.cards.base_card import collapse_colon_packs
from pyNastran.gui.menus.manage_actors import CustomQTableView, Model


class ColorDisplay(QtGui.QWidget):
    """
    http://stackoverflow.com/questions/4624985/how-simply-display-a-qcolor-using-pyqt
    """
    def __init__(self, parent, default_color=None):
        super(ColorDisplay, self).__init__(parent)
        #if default_color is None:
        #default_color = 'red'
        #print("default color", default_color)
        self.color = default_color
        #self.color = QtGui.QColor(*default_color)
        #self.color = (0.1, 0.2, 0.3)
        #self.color = None
        #self.color = 'red'
        #self.color = QtGui.QColor((0.1, 0.2, 0.3))
        #self.update()
        self.setColor(self.color)

    def setColor(self, color):
        #print('setColor -> %s' % str(color))
        if color is not None:
            color = [int(255 * i) for i in color]
        #print('qcolor input -> %s' % str(color))
        self.color = QtGui.QColor(*color)
        self.update()

    def paintEvent(self, event=None):
        painter = QtGui.QPainter(self)
        if self.color is not None:
            painter.setBrush(QtGui.QBrush(self.color))
            painter.drawRect(self.rect())

    def getColorName(self):
        return unicode(self.color.name())


class GroupsModify(QtGui.QDialog):
    """
    +--------------------------+
    |     Groups : Modify      |
    +--------------------------+
    |                          |
    |  Name        xxx Default |
    |  Coords      xxx Default |
    |  Elements    xxx Default |
    |  Color       xxx Default |
    |  Add         xxx Add     |
    |  Remove      xxx Remove  |
    |                          |
    |      Set  OK Cancel      |
    +--------------------------+
    """
    def __init__(self, data, win_parent=None):
        self.win_parent = win_parent
        QtGui.QDialog.__init__(self, win_parent)

        self.win_parent = win_parent
        self.out_data = data

        #self.keys = sorted(data.keys())
        #self.keys = data.keys()
        #keys = self.keys
        self.active_key = 0 #'main'
        print(data)
        self.keys = [group.name for key, group in sorted(iteritems(data))]

        group_obj = data[self.active_key]
        name = group_obj.name

        self.imain = 0
        self.nrows = len(self.keys)

        self._default_name = group_obj.name
        self._default_elements = group_obj.elements
        self.elements_pound = group_obj.elements_pound

        #self._default_coords = data['coords']
        #self._default_color = data['color']
        #self.coords_pound = data['coords_pound']


        self.use_qlist = True

        if self.use_qlist:
            self.table = QtGui.QListWidget(parent=None)
            self.table.clear()
            self.table.addItems(self.keys)
        else:
            header_labels = ['Groups']
            table_model = Model(self.keys, header_labels, self)
            view = CustomQTableView(self) #Call your custom QTableView here
            view.setModel(table_model)
            view.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
            self.table = view


        # table
        if not self.use_qlist:
            header = self.table.horizontalHeader()
            header.setStretchLastSection(True)


        self.setWindowTitle('Groups: Modify')
        self.create_widgets()
        self.create_layout()
        self.set_connections()

        self.on_set_as_main()
        #self.show()

    def create_widgets(self):
        # Name
        self.name = QtGui.QLabel("Name:")
        self.name_edit = QtGui.QLineEdit(str(self._default_name).strip())
        self.name_button = QtGui.QPushButton("Default")

        # Coord
        #self.coords = QtGui.QLabel("Coord IDs:")
        #self.coords_edit = QtGui.QLineEdit(str(self._default_coords).strip())
        #self.coords_button = QtGui.QPushButton("Default")


        # elements
        self.elements = QtGui.QLabel("Element IDs:")
        self.elements_edit = QtGui.QLineEdit(str(self._default_elements).strip())
        self.elements_button = QtGui.QPushButton("Default")

        # add
        self.add = QtGui.QLabel("Add:")
        self.add_edit = QtGui.QLineEdit(str(''))
        self.add_button = QtGui.QPushButton("Add")

        # remove
        self.remove = QtGui.QLabel("Remove:")
        self.remove_edit = QtGui.QLineEdit(str(''))
        self.remove_button = QtGui.QPushButton("Remove")

        # color
        #self.color = QtGui.QLabel("Color:")
        #self.color_edit = QtGui.QPushButton()
        #self.color_edit.setColor(self._default_color)
        #self.color_edit = ColorDisplay(self, self._default_color)
        #self.color_button = QtGui.QPushButton("Default")

        # applies a unique implicitly
        self.eids = parse_patran_syntax(str(self._default_elements), pound=self.elements_pound)
        #self.cids = parse_patran_syntax(str(self._default_coords), pound=self.coords_pound)

        # continuous / discrete
        #self.checkbox_continuous = QtGui.QCheckBox("Continuous")
        #self.checkbox_discrete = QtGui.QCheckBox("Discrete")
        #self.checkbox_discrete.setChecked(self._default_is_discrete)

        # put these in a group
        #checkboxs2 = QtGui.QButtonGroup(self)
        #checkboxs2.addButton(self.checkbox_continuous)
        #checkboxs2.addButton(self.checkbox_discrete)

        # closing
        #self.apply_button = QtGui.QPushButton("Apply")
        self.ok_button = QtGui.QPushButton("Close")
        #self.cancel_button = QtGui.QPushButton("Cancel")

        self.set_as_main_button = QtGui.QPushButton("Set As Main")
        self.create_group_button = QtGui.QPushButton('Create New Group')
        self.delete_group_button = QtGui.QPushButton('Delete Group')

        self.name.setEnabled(False)
        self.name_edit.setEnabled(False)
        self.name_button.setEnabled(False)
        self.elements.setEnabled(False)
        self.elements_button.setEnabled(False)
        self.elements_edit.setEnabled(False)
        self.add.setEnabled(False)
        self.add_button.setEnabled(False)
        self.add_edit.setEnabled(False)
        self.remove.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.remove_edit.setEnabled(False)
        self.delete_group_button.setEnabled(False)
        #self.apply_button.setEnabled(False)
        #self.ok_button.setEnabled(False)


    def create_layout(self):
        grid = QtGui.QGridLayout()
        grid.addWidget(self.name, 0, 0)
        grid.addWidget(self.name_edit, 0, 1)
        grid.addWidget(self.name_button, 0, 2)

        #grid.addWidget(self.coords, 1, 0)
        #grid.addWidget(self.coords_edit, 1, 1)
        #grid.addWidget(self.coords_button, 1, 2)

        grid.addWidget(self.elements, 2, 0)
        grid.addWidget(self.elements_edit, 2, 1)
        grid.addWidget(self.elements_button, 2, 2)

        #grid.addWidget(self.color, 3, 0)
        #grid.addWidget(self.color_edit, 3, 1)
        #grid.addWidget(self.color_button, 3, 2)

        grid.addWidget(self.add, 4, 0)
        grid.addWidget(self.add_edit, 4, 1)
        grid.addWidget(self.add_button, 4, 2)

        grid.addWidget(self.remove, 5, 0)
        grid.addWidget(self.remove_edit, 5, 1)
        grid.addWidget(self.remove_button, 5, 2)


        ok_cancel_box = QtGui.QHBoxLayout()
        #ok_cancel_box.addWidget(self.apply_button)
        ok_cancel_box.addWidget(self.ok_button)
        #ok_cancel_box.addWidget(self.cancel_button)


        main_create_delete = QtGui.QHBoxLayout()
        main_create_delete.addWidget(self.set_as_main_button)
        main_create_delete.addWidget(self.create_group_button)
        main_create_delete.addWidget(self.delete_group_button)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.table)
        vbox.addLayout(grid)
        vbox.addLayout(main_create_delete)
        vbox.addStretch()
        vbox.addLayout(ok_cancel_box)


        self.setLayout(vbox)

    def set_connections(self):
        self.connect(self.name_button, QtCore.SIGNAL('clicked()'), self.on_default_name)
        #self.connect(self.coords_button, QtCore.SIGNAL('clicked()'), self.on_default_coords)
        self.connect(self.elements_button, QtCore.SIGNAL('clicked()'), self.on_default_elements)

        self.connect(self.add_button, QtCore.SIGNAL('clicked()'), self.on_add)
        self.connect(self.remove_button, QtCore.SIGNAL('clicked()'), self.on_remove)

        if self.use_qlist:
            self.connect(self.table, QtCore.SIGNAL('itemClicked(QListWidgetItem *)'), self.on_update_active_key)

        #self.connect(self.color_edit, QtCore.SIGNAL('clicked()'), self.on_edit_color)
        #self.color_edit.clicked.connect(self.on_edit_color)


        #self.connect(self.color_button, QtCore.SIGNAL('clicked()'), self.on_default_color)
        #self.connect(self.apply_button, QtCore.SIGNAL('clicked()'), self.on_apply)
        self.connect(self.ok_button, QtCore.SIGNAL('clicked()'), self.on_ok)
        #self.connect(self.cancel_button, QtCore.SIGNAL('clicked()'), self.on_cancel)

        self.connect(self.set_as_main_button, QtCore.SIGNAL('clicked()'), self.on_set_as_main)
        self.connect(self.create_group_button, QtCore.SIGNAL('clicked()'), self.on_create_group)
        self.connect(self.delete_group_button, QtCore.SIGNAL('clicked()'), self.on_delete_group)

    def on_create_group(self):
        print('on_create_group')
        irow = self.nrows
        new_key = 'Group %s' % irow
        while new_key in self.keys:
            irow += 1
            new_key = 'Group %s' % irow
        irow = self.nrows

        if self.use_qlist:
            self.keys.append(new_key)
            group = Group(
                new_key,
                elements='',
                elements_pound=self.elements_pound,
                editable=True)

            self.out_data[irow] = group
            self.table.reset()
            self.table.addItems(self.keys)
        else:
            self.table.model.addRow(new_key)
        self.nrows += 1

        if self.use_qlist:
            pass
            #item = self.table.getItem(self.)
        else:
            for irow in range(self.nrows):
                check = self.checks[irow]
                is_checked = check.checkState()

                # 0 - unchecked
                # 1 - partially checked (invalid)
                # 2 - checked
                if irow == 0 and is_checked:
                    # TODO: change this to a log
                    print('error deleting group ALL...change this to a log')
                    #self.window_parent.log
                    return
                if is_checked:
                    self.table.hideRow(irow)
                    self.deleted_groups.add(irow)
                    check.setCheckState(0)

            if self.imain > 0 and self.shown_set == set([0]):
                bold = QtGui.QFont()
                bold.setBold(True)
                bold.setItalic(True)

                self.imain = 0
                irow = 0
                check = self.checks[irow]
                name_text = self.names_texts[irow]
                name_text.setFont(bold)
                name_text.setBackground(QtGui.QColor(*self.light_grey))

        #----------------------------------
        # update internal parameters
        #self.out_data = items
        if self.imain >= self.active_key:
            self.imain += 1

        #make the new group the default
        self.active_key = self.nrows - 1

        self.keys = [group.name for key, group in sorted(iteritems(self.out_data))]
        self.recreate_table()

    def recreate_table(self):
        # update gui
        if self.use_qlist:
            #self.table.reset()
            self.table.clear()
            self.table.addItems(self.keys)
            #item = self.table.getItem(self.imain)
            item = self.table.item(self.imain)

            bold = QtGui.QFont()
            bold.setBold(True)
            bold.setItalic(True)
            item.setFont(bold)
            self.table.update()
        else:
            model = self.table.model()
            model.reset()
            for i, key in enumerate(self.keys):
                model.insertRow(i, key)
            #model.setData(self.keys)

        # update key
        name = self.keys[self.active_key]
        self._update_active_key_by_name(name)

    def on_delete_group(self):
        print('on_delete_group - A')
        if self.active_key == 0:
            return

        print('on_delete_group - B')
        #self.deleted_groups.add(self.imain)
        items = {}
        j = 0
        for i, key in sorted(iteritems(self.out_data)):
            if i != self.active_key:
                items[j] = key
                j += 1

        # update internal parameters
        self.out_data = items
        if self.imain >= self.active_key:
            self.imain = max(0, self.imain - 1)
        self.active_key = max(0, self.active_key - 1)
        self.nrows -= 1
        self.keys = [group.name for key, group in sorted(iteritems(items))]

        self.recreate_table()

        ## update gui
        #if self.use_qlist:
            ##self.table.reset()
            #self.table.clear()
            #self.table.addItems(self.keys)
            ##item = self.table.getItem(self.imain)
            #item = self.table.item(self.imain)

            #bold = QtGui.QFont()
            #bold.setBold(True)
            #bold.setItalic(True)
            #item.setFont(bold)
            #self.table.update()
        #else:
            #model = self.table.model()
            #model.reset()
            #for i, key in enumerate(self.keys):
                #model.insertRow(i, key)
            ##model.setData(self.keys)

        # update key
        name = self.keys[self.active_key]
        self._update_active_key_by_name(name)

    def on_set_as_main(self):
        bold = QtGui.QFont()
        bold.setBold(True)
        bold.setItalic(True)

        normal = QtGui.QFont()
        normal.setBold(False)
        normal.setItalic(False)

        if self.use_qlist:
            obj = self.table.item(self.imain)
            obj.setFont(normal)

            self.imain = self.active_key
            obj = self.table.item(self.imain)
            obj.setFont(bold)
        else:
            imain = None
            imain_set = False
            for irow in range(self.nrows):
                check = self.checks[irow]
                name_text = self.names_text[irow]
                is_checked = check.checkState()

                # 0 - unchecked
                # 1 - partially checked (invalid)
                # 2 - checked
                if is_checked and not imain_set:
                    # TODO: change this to a log
                    #self.window_parent.log
                    imain_set = True
                    imain = irow
                    name_text.setFont(bold)
                    name_text.setBackground(QtGui.QColor(*self.light_grey))
                    self.shown_set.add(irow)
                elif irow == self.imain:
                    name_text.setFont(normal)
                    if irow == 0:
                        name_text.setBackground(QtGui.QColor(*self.white))
                        if irow in self.shown_set:
                            self.shown_set.remove(irow)
                    elif imain == 0:
                        name_text.setBackground(QtGui.QColor(*self.white))
                        self.shown_set.remove(imain)
            self.imain = imain

    def closeEvent(self, event):
        event.accept()

    def on_add(self):
        eids, is_valid = self.check_patran_syntax(self.add_edit)
        #adict, is_valid = self.check_patran_syntax_dict(self.add_edit)
        if not is_valid:
            #self.add_edit.setStyleSheet("QLineEdit{background: red;}")
            return

        self.eids = unique(hstack([self.eids, eids]))
        #self.eids = _add(adict, ['e', 'elem', 'element'], self.eids)
        #self.cids = _add(adict, ['c', 'cid', 'coord'], self.cids)
        self._apply_cids_eids()

        self.add_edit.clear()
        self.add_edit.setStyleSheet("QLineEdit{background: white;}")

    def _apply_cids_eids(self):
        #ctext = _get_collapsed_text(self.cids)
        etext = _get_collapsed_text(self.eids)

        #self.coords_edit.setText(str(ctext.lstrip()))
        self.elements_edit.setText(str(etext.lstrip()))

    def on_remove(self):
        eids, is_valid = self.check_patran_syntax(self.remove_edit)
        #adict, is_valid = self.check_patran_syntax_dict(self.remove_edit)
        if not is_valid:
            #self.remove_edit.setStyleSheet("QLineEdit{background: red;}")
            return

        #self.eids = _remove(adict, ['e', 'elem', 'element'], self.eids)
        #self.cids = _remove(adict, ['c', 'cid', 'coord'], self.cids)
        self.eids = setdiff1d(self.eids, eids)
        self._apply_cids_eids()

        self.remove_edit.clear()
        self.remove_edit.setStyleSheet("QLineEdit{background: white;}")

    def on_default_name(self):
        self.name_edit.setText(str(self._default_name))
        self.name_edit.setStyleSheet("QLineEdit{background: white;}")

    #def on_default_coords(self):
        #self.coords_edit.setText(str(self._default_coords))
        #self.coords_edit.setStyleSheet("QLineEdit{background: white;}")

    def on_default_elements(self):
        self.elements_edit.setText(str(self._default_elements))
        self.elements_edit.setStyleSheet("QLineEdit{background: white;}")

    #def on_edit_color(self):
        #c = [int(255 * i) for i in self.text_color]
        #color = QtGui.QColorDialog.getColor(QtGui.QColor(*c), self, "Choose a text color")
        #self.color.SetColor(color)

    #def on_default_color(self):
        #self.color_edit.setColor(self._default_color)
        #self.elements_edit.setStyleSheet("QLineEdit{background: white;}")

    def check_patran_syntax(self, cell, pound=None):
        text = str(cell.text())
        try:
            values = parse_patran_syntax(text, pound=pound)
            cell.setStyleSheet("QLineEdit{background: white;}")
            return values, True
        except ValueError as e:
            cell.setStyleSheet("QLineEdit{background: red;}")
            cell.setToolTip(str(e))
            return None, False

    def check_patran_syntax_dict(self, cell, pound=None):
        text = str(cell.text())
        try:
            value = parse_patran_syntax_dict(text)
            cell.setStyleSheet("QLineEdit{background: white;}")
            cell.setToolTip('')
            return value, True
        except (ValueError, SyntaxError, KeyError) as e:
            cell.setStyleSheet("QLineEdit{background: red;}")
            cell.setToolTip(str(e))
            return None, False

    def check_float(self, cell):
        text = cell.text()
        try:
            value = float(text)
            cell.setStyleSheet("QLineEdit{background: white;}")
            cell.setToolTip('')
            return value, True
        except ValueError:
            cell.setStyleSheet("QLineEdit{background: red;}")
            return None, False

    def check_name(self, cell):
        text = str(cell.text()).strip()
        if len(text):
            cell.setStyleSheet("QLineEdit{background: white;}")
            return text, True
        else:
            cell.setStyleSheet("QLineEdit{background: red;}")
            return None, False

        if self._default_name != text:
            if self._default_name in self.out_data:
                cell.setStyleSheet("QLineEdit{background: white;}")
                return text, True
            else:
                cell.setStyleSheet("QLineEdit{background: red;}")
                return None, False

    def check_format(self, cell):
        text = str(cell.text())

        is_valid = True
        if len(text) < 2:
            is_valid = False
        elif 's' in text.lower():
            is_valid = False
        elif '%' not in text[0]:
            is_valid = False
        elif text[-1].lower() not in ['g', 'f', 'i', 'e']:
            is_valid = False

        try:
            text % 1
            text % .2
            text % 1e3
            text % -5.
            text % -5
        except ValueError:
            is_valid = False

        try:
            text % 's'
            is_valid = False
        except TypeError:
            pass

        if is_valid:
            cell.setStyleSheet("QLineEdit{background: white;}")
            return text, True
        else:
            cell.setStyleSheet("QLineEdit{background: red;}")
            return None, False

    def on_validate(self):
        name, flag0 = self.check_name(self.name_edit)
        elements, flag1 = self.check_patran_syntax(self.elements_edit,
                                                         pound=self.elements_pound)
        #coords_value, flag2 = self.check_patran_syntax(self.coords_edit,
        #pound=self.coords_pound)
        #color = self.color

        if flag0 and flag1:
            self._default_name = name
            self._default_elements = self.eids
            self.out_data['name'] = name
            self.out_data['elements'] = elements
            #self.out_data['coords'] = coords
            self.out_data['clicked_ok'] = True

            #print("name = %r" % self.name_edit.text())
            #print("min = %r" % self.min_edit.text())
            #print("max = %r" % self.max_edit.text())
            #print("format = %r" % self.format_edit.text())
            return True
        return False

    def on_apply(self, force=False):
        passed = self.on_validate()
        if passed or force:
            self.win_parent.on_modify_group(self.out_data)

    def on_ok(self):
        passed = self.on_validate()
        if passed:
            self.close()
            #self.destroy()

    def on_cancel(self):
        self.close()

    def on_update_active_key(self, index):
        self.update_active_key(index)
        #str(index.text())

    def update_active_key(self, index):
        old_obj = self.out_data[self.imain]

        if self.use_qlist:
            name = str(index.text())
        else:
            name = str(index.data().toString())
        #i = self.keys.index(self.active_key)

        self._update_active_key_by_name(name)

    def _update_active_key_by_name(self, name):
        if name in self.keys:
            self.active_key = self.keys.index(name)
        else:
            # we (hopefully) just removed a row
            #self.active_key = self.keys[self.active_key]
            pass

        self.name_edit.setText(name)
        obj = self.out_data[self.active_key]

        self.eids = parse_patran_syntax(obj.elements, pound=obj.elements_pound)
        self._default_elements = obj.elements
        self._apply_cids_eids()

        if name == 'main':
            self.name.setEnabled(False)
            self.name_edit.setEnabled(False)
            self.name_button.setEnabled(False)
            self.elements.setEnabled(False)
            self.elements_button.setEnabled(False)
            self.elements_edit.setEnabled(False)
            self.add.setEnabled(False)
            self.add_button.setEnabled(False)
            self.add_edit.setEnabled(False)
            self.remove.setEnabled(False)
            self.remove_button.setEnabled(False)
            self.remove_edit.setEnabled(False)
            self.delete_group_button.setEnabled(False)
            #self.apply_button.setEnabled(False)
            #self.ok_button.setEnabled(False)
        else:
            self.name.setEnabled(True)
            self.name_edit.setEnabled(True)
            self.name_button.setEnabled(True)
            self.elements.setEnabled(True)
            self.elements_button.setEnabled(True)
            self.elements_edit.setEnabled(True)
            self.add.setEnabled(True)
            self.add_button.setEnabled(True)
            self.add_edit.setEnabled(True)
            self.remove.setEnabled(True)
            self.remove_button.setEnabled(True)
            self.remove_edit.setEnabled(True)
            self.delete_group_button.setEnabled(True)
            #self.apply_button.setEnabled(True)
            #self.ok_button.setEnabled(True)
        # TODO: call default
        #self.elements_edit # obj.eids


        #self.bar_scale_edit.setValue(bar_scale)
        #self.color.setVisible(False)
        #self.point_size_edit.setEnabled(True)
        #self.on_apply(force=True)

def _get_collapsed_text(values):
    singles, doubles = collapse_colon_packs(values)
    text = ' '.join([str(s) for s in singles]) + ' '
    text += ' '.join([''.join([str(doublei) for doublei in double]) for double in doubles])
    return text

def _add(adict, keys, values_to_add):
    value_stack = []
    for key in keys:
        if key not in adict:
            continue
        values = adict[key]
        value_stack.append(values)
    if value_stack:
        value_stack.append(values_to_add)
        values_add = unique(hstack(value_stack))
        return values_add
    return values_to_add

def _simple_add(values_to_add):
    value_stack.append(values_to_add)
    values_add = unique(hstack(value_stack))
    return values_add

def _remove(adict, keys, values_to_remove):
    value_stack = []
    for key in keys:
        if key not in adict:
            continue
        value_stack.append(adict[key])
    if value_stack:
        values_remove = unique(hstack(value_stack))
        return setdiff1d(values_to_remove, values_remove)
    return values_to_remove

class Group(object):
    def __init__(self, name, elements, elements_pound, editable=True):
        self.name = name
        #self.cids = [0]
        assert isinstance(elements, (str, unicode)), elements
        self.elements = elements
        self.elements_pound = elements_pound
        self.editable = editable

    def __repr__(self):
        msg = 'Group:\n'
        msg += '  name: %s\n' % self.name
        msg += '  editable: %s\n' % self.editable
        #msg += '  cids: [%s]\n' % _get_collapsed_text(self.cids).strip()
        msg += '  elements: [%s]\n' % self.elements
        #msg += '  elements: [%s]\n' % _get_collapsed_text(self.elements).strip()
        msg += '  elements_pound: %s\n' % self.elements_pound
        return msg

def main():
    # kills the program when you hit Cntl+C from the command line
    # doesn't save the current state as presumably there's been an error
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    import sys
    # Someone is launching this directly
    # Create the QApplication
    app = QtGui.QApplication(sys.argv)

    d = {
        0 : Group(name='main', elements='1:#', elements_pound='103', editable=False),
        1 : Group(name='wing', elements='1:10', elements_pound='103', editable=True),
        2 : Group(name='fuselage1', elements='50:60', elements_pound='103', editable=True),
        3 : Group(name='fuselage2', elements='50:60', elements_pound='103', editable=True),
        4 : Group(name='fuselage3', elements='50:60', elements_pound='103', editable=True),
        5 : Group(name='fuselage4', elements='50:60', elements_pound='103', editable=True),
        6 : Group(name='fuselage5', elements='50:60', elements_pound='103', editable=True),
        7 : Group(name='fuselage6', elements='50:60', elements_pound='103', editable=True),
        8 : Group(name='fuselage7', elements='50:60', elements_pound='103', editable=True),
        9 : Group(name='fuselage8', elements='50:60', elements_pound='103', editable=True),
        10 : Group(name='fuselage9', elements='50:60', elements_pound='103', editable=True),
        11 : Group(name='fuselage10', elements='50:60', elements_pound='103', editable=True),
        12 : Group(name='fuselage11', elements='50:60', elements_pound='103', editable=True),
        13 : Group(name='fuselage12', elements='50:60', elements_pound='103', editable=True),
        14 : Group(name='fuselage13', elements='50:60', elements_pound='103', editable=True),
        15 : Group(name='fuselage14', elements='50:60', elements_pound='103', editable=True),
    }
    main_window = GroupsModify(d)
    main_window.show()
    # Enter the main loop
    app.exec_()

if __name__ == "__main__":
    main()
