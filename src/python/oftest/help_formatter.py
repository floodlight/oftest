import optparse

# Don't wrap description text to give us more control over newlines.
class HelpFormatter(optparse.IndentedHelpFormatter):
    def format_description(self, description):
        if description:
            indent = " "*self.current_indent
            return indent + description
        else:
            return None
