import React, { useEffect, useRef, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ColorRing } from "react-loader-spinner";
import { IoCheckmarkCircle, IoCloseCircle } from "react-icons/io5";
import { useNavigate } from "react-router-dom";

export interface BuildPopupProps {
  file_key: string;
  open: boolean;
  setOpen: (isOpen: boolean) => void;
}

export const BuildPopup: React.FC<BuildPopupProps> = ({
  file_key,
  open,
  setOpen,
}) => {
  const [logs, setLogs] = useState<string[]>([]);
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const logsEndRef = useRef<HTMLDivElement | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!open) {
      setLogs([]); // Clear logs when dialog is closed
      setStatus("loading");
      return;
    }

    if (file_key) {
      const fetchLogs = async () => {
        setStatus("loading");
        try {
          const response = await fetch(`/api/build-container/${file_key}`, {
            method: "POST",
          });

          if (!response.body) {
            throw new Error("No response body received.");
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder("utf-8");
          let done = false;

          while (!done) {
            const { value, done: readerDone } = await reader.read();
            done = readerDone;

            if (value) {
              const chunk = decoder.decode(value, { stream: true });
              const lines = chunk.split("\n");

              setLogs((prevLogs) => [...prevLogs, ...lines]);

              // Check for "ERROR:" in the chunk
              if (lines.some((line) => line.includes("ERROR:"))) {
                setStatus("error");
                return;
              }
            }
          }

          if (response.ok) {
            setStatus("success");
            submitBenchTask(file_key);
          } else {
            setStatus("error");
          }
        } catch (error) {
          console.error("Error fetching logs:", error);
          setLogs((prevLogs) => [...prevLogs, "Error fetching logs."]);
          setStatus("error");
        }
      };

      fetchLogs();
    }
  }, [open, file_key]);

  // Scroll to bottom whenever logs update
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  const submitBenchTask = async (image: string) => {
    try {
      const response = await fetch(`/api/benchmark?image=${image}`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Task ID:", data.task_id);
    } catch (error) {
      console.error("Error calling benchmark:", error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Building container...</DialogTitle>
          <DialogDescription>
            <div className="flex flex-row justify-between">
              <p className="my-auto">
                {status === "loading" &&
                  "Please wait as your container is being built."}
                {status === "success" && "Container built successfully!"}
                {status === "error" &&
                  "An error occurred when building container."}
              </p>
              {status === "loading" && (
                <ColorRing
                  visible={true}
                  height="40"
                  width="40"
                  ariaLabel="color-ring-loading"
                  wrapperStyle={{}}
                  wrapperClass="color-ring-wrapper"
                  colors={[
                    "#4A90E2",
                    "#4A90E2",
                    "#4A90E2",
                    "#4A90E2",
                    "#4A90E2",
                  ]}
                />
              )}
              {status === "success" && (
                <IoCheckmarkCircle className="text-green-400 text-3xl my-auto" />
              )}
              {status === "error" && (
                <IoCloseCircle className="text-red-400 text-3xl my-auto" />
              )}
            </div>
            <div
              style={{
                marginTop: "1rem",
                padding: "1rem",
                backgroundColor: "#f9f9f9",
                borderRadius: "8px",
                maxHeight: "300px",
                overflowY: "auto",
                fontFamily: "monospace",
                wordBreak: "break-word",
              }}
            >
              {logs.length > 0 ? (
                <>
                  {logs.map((log, index) => (
                    <p key={index}>{log}</p>
                  ))}
                  {/* Invisible div to scroll to */}
                  <div ref={logsEndRef} />
                </>
              ) : status === "loading" ? (
                <p>Waiting for logs...</p>
              ) : (
                <p>No logs available.</p>
              )}
            </div>
          </DialogDescription>
        </DialogHeader>
        {status === "success" && (
          <div className="mt-4 flex justify-end">
            <Button onClick={() => navigate(`/submission/${file_key}`)}>
              Go to submission
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
