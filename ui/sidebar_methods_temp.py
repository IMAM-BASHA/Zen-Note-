    def toggle_archived_view(self):
        """Toggle between Main and Archived views."""
        self.showing_archived = not self.showing_archived
        
        if self.showing_archived:
            self.title_label.setText("Archived")
            self.back_btn.setVisible(True)
            self.add_btn.setVisible(False) # Hide "New Folder" in archive view
        else:
            self.title_label.setText("NOTEBOOKS")
            self.back_btn.setVisible(False)
            self.add_btn.setVisible(True)
            
        self.refresh_list()

    def on_item_clicked(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        
        if data == "ARCHIVED_ROOT":
            self.toggle_archived_view()
        else:
            # It's a folder ID
            folder_id = data
            self.folderSelected.emit(folder_id)
