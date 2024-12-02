import { ColumnDef } from "@tanstack/react-table";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import { Button } from "@/components/ui/button"
import { ArrowUpDown } from "lucide-react"
import { Badge } from "@/components/ui/badge"

import { IoCheckmarkCircle, IoCloseCircle } from "react-icons/io5";

export type Result = {
    submission_id: string
    name: string
    submission_name: string
    runtime: number
    ratio: number
    accuracy: number
    status: "pending" | "success" | "failed"
}

const computeMinMax = (rows: any[], columnId: string) => {
    const values = rows.map((row) => parseFloat(row.getValue(columnId)));
    return {
      min: Math.min(...values),
      max: Math.max(...values),
    };
};

const getTailwindColor = (value: number, min: number, max: number) => {
    const ratio = (value - min) / (max - min);
    switch (true) {
        case ratio <= 0.125:
            return "bg-red-400";
        case ratio <= 0.25:
            return "bg-red-300";
        case ratio <= 0.375:
            return "bg-red-200";
        case ratio <= 0.5:
            return "bg-red-100";
        case ratio <= 0.625:
            return "bg-green-100";
        case ratio <= 0.75:
            return "bg-green-200";
        case ratio <= 0.875:
            return "bg-green-300";
        default:
            return "bg-green-400";
    }
};

export const columns: ColumnDef<Result>[] = [
    {
        accessorKey: "submission_id",
        header: "ID",
        cell: ({ row }) => {
            const value = row.getValue("submission_id") as string
            const subvalue = value.split("-").pop() as string
            return (
                <div className="text-center">
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger>
                                <Badge className="p-1 font-mono" variant="secondary">{subvalue}</Badge>
                            </TooltipTrigger>
                            <TooltipContent>
                                <p className="font-mono">{value}</p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                </div>
            )
        }
    },
    {
        accessorKey: "name",
        header: "Name",
    },
    {
        accessorKey: "submission_name",
        header: "Submission Name",
    },
    {
        accessorKey: "runtime",
        header: ({ column }) => {
            return (
              <Button
                variant="ghost"
                onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
              >
                Runtime
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            )
        },
        cell: ({ row, table }) => {
            const { min, max } = computeMinMax(table.getRowModel().rows, "runtime")
            const value = parseFloat(row.getValue("runtime"))
            const backgroundColor = getTailwindColor(value, max, min)
            return (
                <div className={`${backgroundColor} p-2 rounded text-right font-medium`}>
                    {value}s
                </div>
            );
        }
    },
    {
        accessorKey: "ratio",
        header: ({ column }) => {
            return (
              <Button
                variant="ghost"
                onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
              >
                Deflate Ratio
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            )
        },
        cell: ({ row, table }) => {
            const { min, max } = computeMinMax(table.getRowModel().rows, "ratio")
            const value = parseFloat(row.getValue("ratio"))
            const backgroundColor = getTailwindColor(value, min, max)
            return (
                <div className={`${backgroundColor} p-2 rounded text-right font-medium`}>
                    {(value * 100).toFixed(2)}%
                </div>
            );
        }
    },
    {
        accessorKey: "accuracy",
        header: ({ column }) => {
            return (
              <Button
                variant="ghost"
                onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
              >
                Search Accuracy
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            )
        },
        cell: ({ row, table }) => {
            const { min, max } = computeMinMax(table.getRowModel().rows, "accuracy")
            const value = parseFloat(row.getValue("accuracy"))
            const backgroundColor = getTailwindColor(value, min, max)
            return (
                <div className={`${backgroundColor} p-2 rounded text-right font-medium`}>
                    {(value * 100).toFixed(2)}%
                </div>
            );
        }
    },
    {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => {
          const value = row.getValue("status");
          return (
            <>
              {value === "success" && (
                <IoCheckmarkCircle className="text-green-400 text-3xl m-auto" />
              )}
              {value === "error" && (
                <IoCloseCircle className="text-red-400 text-3xl m-auto" />
              )}
            </>
          );
        },
    }
]