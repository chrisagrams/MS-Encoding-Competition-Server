import React, { useEffect, useRef, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

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
  const [loading, setLoading] = useState<boolean>(false);
  const logsEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) {
      setLogs([]); // Clear logs when dialog is closed
      return;
    }

    if (file_key) {
      setLoading(true);
      const fetchLogs = async () => {
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
              setLogs((prevLogs) => [...prevLogs, ...chunk.split("\n")]);
            }
          }

          setLoading(false);
        } catch (error) {
          console.error("Error fetching logs:", error);
          setLogs((prevLogs) => [...prevLogs, "Error fetching logs."]);
          setLoading(false);
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

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Building container...</DialogTitle>
          <DialogDescription>
            <p>Please wait as your container is being built.</p>
            <div
              style={{
                marginTop: "1rem",
                padding: "1rem",
                backgroundColor: "#f9f9f9",
                borderRadius: "8px",
                maxHeight: "300px",
                overflowY: "auto",
                fontFamily: "monospace",
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
              ) : loading ? (
                <p>Waiting for logs...</p>
              ) : (
                <p>No logs available.</p>
              )}
            </div>
          </DialogDescription>
        </DialogHeader>
      </DialogContent>
    </Dialog>
  );
};
