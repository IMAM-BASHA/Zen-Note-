    def apply_level_1(self):
        """Apply Level 1 formatting to selection with hierarchical numbering."""
        cursor = self.editor.textCursor()
        
        if not cursor.hasSelection():
            QMessageBox.warning(self, "No Selection", "Please select text to apply Level 1.")
            return
        
        selected_text = cursor.selectedText()
        
        # Calculate next Level 1 number
        level1_count = self._count_levels_in_document(1)
        new_number = f"{self.base_note_index}.{level1_count + 1}"
        
        # Create span with level data
        span_html = (
            f'<span class="lvl-number lvl-1" data-lvl="1" data-text="{selected_text}" '
            f'style="background-color: {self.level1_color.name()}; padding: 2px 5px; border-radius: 3px; font-weight: bold;">'
            f'{new_number} {selected_text}</span>'
        )
        
        cursor.insertHtml(span_html + " ")
        self.editor.setFocus()
        
        # Trigger renumbering to ensure consistency
        self.renumber_all_levels()
    
    def apply_level_2(self):
        """Apply Level 2 formatting to selection with hierarchical numbering."""
        # First, check if at least one Level 1 exists
        level1_count = self._count_levels_in_document(1)
        if level1_count == 0:
            QMessageBox.warning(
                self, 
                "No Level 1 Found", 
                "Level 2 requires at least one Level 1 to exist in the document.\nPlease apply Level 1 first."
            )
            return
        
        cursor = self.editor.textCursor()
        
        if not cursor.hasSelection():
            QMessageBox.warning(self, "No Selection", "Please select text to apply Level 2.")
            return
        
        selected_text = cursor.selectedText()
        
        # Calculate Level 1 and Level 2 counters
        current_level1, level2_count = self._get_current_level_context(cursor)
        
        if current_level1 == 0:
            current_level1 = level1_count  # Default to last Level 1 if not found
        
        new_number = f"{self.base_note_index}.{current_level1}.{level2_count + 1}"
        
        # Create span with level data
        span_html = (
            f'<span class="lvl-number lvl-2" data-lvl="2" data-text="{selected_text}" '
            f'style="background-color: {self.level2_color.name()}; padding: 2px 5px; border-radius: 3px; font-weight: bold;">'
            f'{new_number} {selected_text}</span>'
        )
        
        cursor.insertHtml(span_html + " ")
        self.editor.setFocus()
        
        # Trigger renumbering to ensure consistency
        self.renumber_all_levels()
    
    def _count_levels_in_document(self, level):
        """Count how many level markers of a specific level exist in the document."""
        html = self.editor.toHtml()
        import re
        pattern = rf'data-lvl="{level}"'
        return len(re.findall(pattern, html))
    
    def _get_current_level_context(self, cursor):
        """
        Determine the current Level 1 context and Level 2 count for cursor position.
        Returns: (current_level1_number, level2_count_under_that_level1)
        """
        doc = self.editor.document()
        cursor_pos = cursor.position()
        
        current_level1 = 0
        level2_count = 0
        
        html = doc.toHtml()
        import re
        
        # Find all level markers with their approximate positions
        # This is a simplified approach - we parse HTML to extract levels in order
        level1_pattern = r'<span[^>]*data-lvl="1"'
        level2_pattern = r'<span[^>]*data-lvl="2"'
        
        # Count Level 1s before cursor (approximation)
        html_before_cursor = html[:cursor_pos * 10]  # Rough estimate
        level1_matches = re.findall(level1_pattern, html_before_cursor)
        current_level1 = len(level1_matches)
        
        # Count Level 2s after last Level 1
        if current_level1 > 0:
            # Find position of last Level 1
            all_level1 = list(re.finditer(level1_pattern, html))
            if all_level1:
                last_l1_pos = all_level1[-1].end()
                html_after_last_l1 = html[last_l1_pos:cursor_pos * 10]
                level2_matches = re.findall(level2_pattern, html_after_last_l1)
                level2_count = len(level2_matches)
        
        return (current_level1, level2_count)
    
    def renumber_all_levels(self):
        """
        Traverse the document and renumber all Level 1 and Level 2 spans
        based on the current base_note_index.
        """
        if self.base_note_index == 0:
            return  # No base index set yet
        
        html = self.editor.toHtml()
        import re
        
        level1_counter = 0
        level2_counter = 0
        current_level1 = 0
        
        def replace_level1(match):
            nonlocal level1_counter, level2_counter, current_level1
            level1_counter += 1
            current_level1 = level1_counter
            level2_counter = 0  # Reset Level 2 counter
            
            # Extract original text from data-text attribute
            text_match = re.search(r'data-text="([^"]*)"', match.group(0))
            original_text = text_match.group(1) if text_match else "Text"
            
            # Extract style
            style_match = re.search(r'style="([^"]*)"', match.group(0))
            style = style_match.group(1) if style_match else f"background-color: {self.level1_color.name()}; padding: 2px 5px; border-radius: 3px; font-weight: bold;"
            
            new_number = f"{self.base_note_index}.{level1_counter}"
            return (
                f'<span class="lvl-number lvl-1" data-lvl="1" data-text="{original_text}" style="{style}">'
                f'{new_number} {original_text}</span>'
            )
        
        def replace_level2(match):
            nonlocal level2_counter
            level2_counter += 1
            
            # Extract original text
            text_match = re.search(r'data-text="([^"]*)"', match.group(0))
            original_text = text_match.group(1) if text_match else "Text"
            
            # Extract style
            style_match = re.search(r'style="([^"]*)"', match.group(0))
            style = style_match.group(1) if style_match else f"background-color: {self.level2_color.name()}; padding: 2px 5px; border-radius: 3px; font-weight: bold;"
            
            new_number = f"{self.base_note_index}.{current_level1}.{level2_counter}"
            return (
                f'<span class="lvl-number lvl-2" data-lvl="2" data-text="{original_text}" style="{style}">'
                f'{new_number} {original_text}</span>'
            )
        
        # Replace all Level 1 spans
        html = re.sub(
            r'<span class="lvl-number lvl-1"[^>]*>.*?</span>',
            replace_level1,
            html,
            flags=re.DOTALL
        )
        
        # Reset counters for Level 2 processing
        level1_counter = 0
        level2_counter = 0
        current_level1 = 0
        
        # Need to reprocess to handle Level 2 correctly per Level 1
        # Split by Level 1 markers and process Level 2 within each section
        parts = re.split(r'(<span class="lvl-number lvl-1"[^>]*>.*?</span>)', html, flags=re.DOTALL)
        
        result = []
        for i, part in enumerate(parts):
            if 'data-lvl="1"' in part:
                level1_counter += 1
                current_level1 = level1_counter
                level2_counter = 0
                result.append(part)
            elif 'data-lvl="2"' in part:
                # This part contains Level 2 markers - renumber them
                def replace_l2_in_section(m):
                    nonlocal level2_counter
                    level2_counter += 1
                    text_match = re.search(r'data-text="([^"]*)"', m.group(0))
                    original_text = text_match.group(1) if text_match else "Text"
                    style_match = re.search(r'style="([^"]*)"', m.group(0))
                    style = style_match.group(1) if style_match else f"background-color: {self.level2_color.name()}; padding: 2px 5px; border-radius: 3px; font-weight: bold;"
                    new_number = f"{self.base_note_index}.{current_level1}.{level2_counter}"
                    return f'<span class="lvl-number lvl-2" data-lvl="2" data-text="{original_text}" style="{style}">{new_number} {original_text}</span>'
                
                part = re.sub(r'<span class="lvl-number lvl-2"[^>]*>.*?</span>', replace_l2_in_section, part, flags=re.DOTALL)
                result.append(part)
            else:
                result.append(part)
        
        final_html = ''.join(result)
        
        # Set the HTML back (preserve cursor position)
        cursor_pos = self.editor.textCursor().position()
        self.editor.setHtml(final_html)
        cursor = self.editor.textCursor()
        cursor.setPosition(min(cursor_pos, len(self.editor.toPlainText())))
        self.editor.setTextCursor(cursor)
    
    def set_base_note_index(self, index):
        """
        Called by MainWindow to set the current note's index.
        Triggers renumbering of all levels.
        """
        self.base_note_index = index
        self.renumber_all_levels()
