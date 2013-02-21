from aqt import mw
from aqt import editor
from anki.hooks import wrap
from anki.utils import splitFields, stripHTMLMedia
from anki.utils import json
import urllib2

def mySetup(self, note, hide=True, focus=False):
    self.prevAutocomplete = ""

    # only initialize the autocompleter on Add Cards not in browser
    if self.note and self.addMode:
        self.web.eval("""
            document.styleSheets[0].addRule('.autocomplete', 'margin: 0.3em 0 1.0em 0;');
            document.styleSheets[0].addRule('.autocomplete .copy', 'color: blue; text-decoration: underline; cursor: pointer;');

            // every second send the current state over
            setInterval(function () {
                if (currentField) {
                    var r = {
                        text: currentField.innerHTML,
                    };

                    py.run("autocomplete:" + JSON.stringify(r));
                }
            }, 1000);
        """)

def myBridge(self, str, _old=None):
    if str.startswith("autocomplete"):
        (type, jsonText) = str.split(":", 1)
        result = json.loads(jsonText)
        text = self.mungeHTML(result['text'])

        # bail out if the user hasn't actually changed the field
        previous = "%d:%s" % (self.currentField, text)
        if self.prevAutocomplete == previous:
            return
        self.prevAutocomplete = previous

        if text == "" or self.note is None:
            self.web.eval("$('.autocomplete').remove();");
            return

        # find a value from the same model and field whose
        # prefix is what the user typed so far
        query = "'note:%s' '%s:%s*'" % (
            self.note.model()['name'],
            self.note.model()['flds'][self.currentField]['name'],
            text)

        col = self.note.col
        res = col.findCards(query, order=True)

        if len(res) == 0:
            self.web.eval("$('.autocomplete').remove();");
            return

        # pull out the full value
        field = col.getCard(res[0]).note().fields[self.currentField]

        escaped = json.dumps(field)

        self.web.eval("""
            $('.autocomplete').remove();

            if (currentField) {
                $('<div class="autocomplete"><span class="copy">' + %s + '</span></div>').click(function () { currentField.innerHTML = %s }).insertAfter(currentField)
            }
        """
        % (escaped, escaped))
    else:
        _old(self, str)

editor.Editor.bridge = wrap(editor.Editor.bridge, myBridge, 'around')
editor.Editor.setNote = wrap(editor.Editor.setNote, mySetup, 'after')

