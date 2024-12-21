import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import hljs from "highlight.js";
import he from "he";
import "highlight.js/styles/github.css";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { Button } from "@/components/ui/button"
import { ChevronsUpDown } from "lucide-react"
import { Result } from "./columns"
import { IoCheckmarkCircle, IoCloseCircle, IoTime } from "react-icons/io5"


const parseHighlightedCode = (highlightedCode: string) =>
  highlightedCode.split(/(<span.*?>.*?<\/span>)/g).map((token, index) => {
    if (token.startsWith("<span")) {
      const div = document.createElement("div");
      div.innerHTML = token;
      const span = div.firstChild as HTMLElement;
      if (span) {
        return (
          <span key={index} className={span.className}>
            {span.innerText}
          </span>
        );
      }
    }
    return token;
  });

const highlightCode = (code: string) => {
  const decodedCode = he.decode(code);
  const highlighted = hljs.highlight(decodedCode, { language: "python" }).value;
  const fullyDecoded = he.decode(highlighted);
  return parseHighlightedCode(fullyDecoded);
};

export const CodeBlock: React.FC<{ code?: string }> = ({ code }) => (
  <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6 overflow-auto">
    <pre>
      <code>{code ? highlightCode(code) : "Loading..."}</code>
    </pre>
  </div>
);

export const Submission = () => {
  const { uuid } = useParams();
  const [files, setFiles] = useState<{ encode?: string; decode?: string }>({});
  const [resultData, setResultData] = useState<Result>()
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const response = await fetch(`/api/submission-source?id=${uuid}`);
        if (!response.ok) {
          throw new Error(`Error: ${response.statusText}`);
        }
        const data = await response.json();
        setFiles({ encode: data["encode.py"], decode: data["decode.py"] });
      } catch (err: any) {
        setError(err.message || "Failed to fetch files.");
      }
    };
    fetchFiles();
  }, [uuid]);

  useEffect(() => {
    const fetchData = async () => {
        try {
            const response = await fetch(`/api/result?id=${uuid}`); 
            
            if (!response.ok) {
                throw new Error('Failed to get results.');
            }

            const resultData: Result = await response.json();
            setResultData(resultData);
        } catch (err) {
            console.error('Error fetching data:', err);
        } finally {
        }
    };
    fetchData();
    const intervalId = setInterval(fetchData, 1000);
    return () => clearInterval(intervalId);
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Submission</CardTitle>
        <CardDescription>{uuid}</CardDescription>
      </CardHeader>
      <CardContent>
        {error && <p style={{ color: "red" }}>{error}</p>}
        {!error && (
          <>
            <ResizablePanelGroup direction="horizontal">
              <ResizablePanel className="px-3">
                <h3 className="text-xl font-bold">Code</h3>
                <Collapsible>
                  <CollapsibleTrigger asChild>
                  <div className="flex row">
                    <h3 className="my-auto cursor-pointer font-mono">encode.py</h3>
                    <Button variant="ghost" size="sm">
                      <ChevronsUpDown className="h-4 w-4" />
                    </Button>
                  </div>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    {files.encode && (
                        <CodeBlock code={files.encode} />
                    )}
                  </CollapsibleContent>
                </Collapsible>
                <Collapsible>
                <CollapsibleTrigger asChild>
                  <div className="flex row">
                    <h3 className="my-auto cursor-pointer font-mono">decode.py</h3>
                    <Button variant="ghost" size="sm">
                      <ChevronsUpDown className="h-4 w-4" />
                    </Button>
                  </div>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    {files.decode && (
                        <CodeBlock code={files.decode} />
                    )}
                  </CollapsibleContent>
                </Collapsible>
              </ResizablePanel>
              <ResizableHandle />
              <ResizablePanel className="px-3">
                <div className="flex justify-between">
                  <h3 className="text-xl font-bold">Result</h3>
                  <div className="flex gap-2">
                    <p className="my-auto">Status: </p>
                    {resultData?.status === "success" && (
                        <IoCheckmarkCircle className="text-green-400 text-3xl" />
                    )}
                    {resultData?.status === "failed" && (
                        <IoCloseCircle className="text-red-400 text-3xl" />
                    )}
                    {resultData?.status === "pending" && (
                        <IoTime className="text-yellow-400 text-3xl" />
                    )}
                  </div>
                </div>
                <div>
                  
                </div>
              </ResizablePanel>
            </ResizablePanelGroup>
          </>
        )}
      </CardContent>
      <CardFooter></CardFooter>
    </Card>
  );
};
