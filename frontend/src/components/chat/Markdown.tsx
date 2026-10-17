import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/** Model answers are Markdown. react-markdown never renders raw HTML, so this is XSS-safe. */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ node: _node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" />,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
