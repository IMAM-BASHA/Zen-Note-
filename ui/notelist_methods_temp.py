    def toggle_archived_view(self):
        """Toggle between Main and Archived views."""
        self.showing_archived = not self.showing_archived
        
        if self.showing_archived:
            self.back_btn.setVisible(True)
            self.new_note_btn.setVisible(False)
        else:
            self.back_btn.setVisible(False)
            self.new_note_btn.setVisible(True)
            
        self.filter_notes(self.search_input.text())

    def on_item_clicked(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        
        if data == "ARCHIVED_ROOT":
            self.toggle_archived_view()
        else:
            note_id = data
            self.noteSelected.emit(note_id)
