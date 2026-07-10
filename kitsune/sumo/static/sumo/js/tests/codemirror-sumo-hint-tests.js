import { expect } from "chai";

import CodeMirror from "codemirror";
// Importing the module registers the "sumo" hint helper on CodeMirror.
import "sumo/js/codemirror.sumo-hint";

// A minimal stand-in for the CodeMirror editor. The sumo hint helper only reads
// the cursor and the document's lines, so a real editor instance isn't needed.
function fakeEditor(lines, cursor) {
  return {
    getCursor: () => cursor,
    getLine: (n) => lines[n],
    firstLine: () => 0,
    lastLine: () => lines.length - 1,
  };
}

describe("codemirror sumo hint", () => {
  const hint = CodeMirror.hint.sumo;

  it("suggests matching words and skips the word under the cursor", () => {
    // The cursor sits just after the first "foo", which also appears verbatim
    // on the same line. That used to hang the page: the loop's `continue`
    // skipped the regex advance, so re.exec() never moved past the match.
    const editor = fakeEditor(["foo food foobar"], { line: 0, ch: 3 });

    const result = hint(editor);

    expect(result.list).to.deep.equal(["food", "foobar"]);
    expect(result.list).to.not.include("foo");
    expect(result.from.line).to.equal(0);
    expect(result.from.ch).to.equal(0);
    expect(result.to.ch).to.equal(3);
  });

  it("gathers matching words from other lines", () => {
    const editor = fakeEditor(["hello", "help", "he"], { line: 2, ch: 2 });

    const result = hint(editor);

    expect(result.list).to.have.members(["hello", "help"]);
    expect(result.list).to.not.include("he");
  });

  it("returns no suggestions when only the current word matches", () => {
    const editor = fakeEditor(["xyz"], { line: 0, ch: 3 });

    const result = hint(editor);

    expect(result.list).to.deep.equal([]);
  });
});
