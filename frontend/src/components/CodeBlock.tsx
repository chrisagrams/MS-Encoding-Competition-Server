import hljs from "highlight.js"
import "highlight.js/styles/github.css"
import he from "he"

const parseHighlightedCode = (highlightedCode: string): React.ReactNode[] => {
    return highlightedCode.split(/(<span.*?>.*?<\/span>)/g).map((token, index) => {
      if (token.startsWith("<span")) {
        const div = document.createElement("div")
        div.innerHTML = token
        const span = div.firstChild as HTMLElement
        if (span) {
          return (
            <span key={index} className={span.className}>
              {span.innerText}
            </span>
          );
        }
      }
      return token
    });
}

const highlightCode = (code: string) => {
    const decodedCode = he.decode(code)
    const highlighted = hljs.highlight(decodedCode, { language: "python" }).value
    const fullyDecoded = he.decode(highlighted)
    return parseHighlightedCode(fullyDecoded)
}

export const CodeBlock: React.FC<{ code?: string }> = ({ code }) => (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6 overflow-auto">
      <pre>
        <code>{code ? highlightCode(code) : "Loading..."}</code>
      </pre>
    </div>
  );
  