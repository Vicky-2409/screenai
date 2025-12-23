import DOMPurify from "dompurify";
import {
  BtnBold,
  BtnBulletList,
  BtnItalic,
  BtnLink,
  BtnNumberedList,
  BtnUnderline,
  Editor,
  EditorProvider,
  Toolbar,
} from "react-simple-wysiwyg";

export function RichTextEditor({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (html: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-300 bg-white text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 [&_.rsw-ce]:min-h-[110px] [&_.rsw-ce]:px-3 [&_.rsw-ce]:py-2 [&_.rsw-toolbar]:rounded-t-xl [&_.rsw-toolbar]:border-slate-200 dark:[&_.rsw-toolbar]:border-slate-700 dark:[&_.rsw-toolbar]:bg-slate-900">
      <EditorProvider>
        <Editor
          value={value}
          placeholder={placeholder}
          // Sanitize on every change so we never persist unsafe markup.
          onChange={(e) => onChange(DOMPurify.sanitize(e.target.value))}
        >
          <Toolbar>
            <BtnBold />
            <BtnItalic />
            <BtnUnderline />
            <BtnBulletList />
            <BtnNumberedList />
            <BtnLink />
          </Toolbar>
        </Editor>
      </EditorProvider>
    </div>
  );
}

/** Render trusted-after-sanitization HTML produced by the editor. */
export function HtmlContent({ html, className }: { html: string; className?: string }) {
  if (!html) return null;
  const clean = DOMPurify.sanitize(html);
  return (
    <div
      className={className ?? "prose-sm max-w-none text-sm text-slate-600 dark:text-slate-300 [&_a]:text-brand-600 [&_li]:ml-4 [&_ol]:list-decimal [&_ul]:list-disc"}
      dangerouslySetInnerHTML={{ __html: clean }}
    />
  );
}
