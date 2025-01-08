import { ColumnDef, Row } from "@tanstack/react-table"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import { Button } from "@/components/ui/button"
import { ArrowUpDown } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

import { IoCheckmarkCircle, IoCloseCircle, IoTime } from "react-icons/io5"
import { Result } from "@/types"


const computeMinMax = (rows: Row<Result>[], columnId: string) => {
    const values = rows.map((row) => parseFloat(row.getValue(columnId)))
    return {
      min: Math.min(...values),
      max: Math.max(...values),
    }
}

const getTailwindColor = (value: number, min: number, max: number) => {
    const ratio = (value - min) / (max - min)
    switch (true) {
        case ratio <= 0.125:
            return "bg-red-400"
        case ratio <= 0.25:
            return "bg-red-300"
        case ratio <= 0.375:
            return "bg-red-200"
        case ratio <= 0.5:
            return "bg-red-100"
        case ratio <= 0.625:
            return "bg-green-100"
        case ratio <= 0.75:
            return "bg-green-200"
        case ratio <= 0.875:
            return "bg-green-300"
        default:
            return "bg-green-400"
    }
}

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
        accessorKey: "encoding_runtime",
        header: ({ column }) => {
            return (
              <Button
                variant="ghost"
                onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
              >
                Encoding Runtime
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            )
        },
        cell: ({ row, table }) => {
            const { min, max } = computeMinMax(table.getRowModel().rows, "encoding_runtime")
            const value = row.getValue("encoding_runtime") as string
            if (value === null) {
                return (
                    <Skeleton className="h-9 rounded" />
                )
            }
            const numericValue = parseFloat(value)
            const backgroundColor = getTailwindColor(numericValue, max, min)
            return (
                <div className={`${backgroundColor} p-2 rounded text-right font-medium`}>
                    {numericValue.toFixed(2)}s
                </div>
            )
        }
    },
    {
        accessorKey: "decoding_runtime",
        header: ({ column }) => {
            return (
              <Button
                variant="ghost"
                onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
              >
                Decoding Runtime
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            )
        },
        cell: ({ row, table }) => {
            const { min, max } = computeMinMax(table.getRowModel().rows, "decoding_runtime")
            const value = row.getValue("decoding_runtime") as string
            if (value === null) {
                return (
                    <Skeleton className="h-9 rounded" />
                )
            }
            const numericValue = parseFloat(value)
            const backgroundColor = getTailwindColor(numericValue, max, min)
            return (
                <div className={`${backgroundColor} p-2 rounded text-right font-medium`}>
                    {numericValue.toFixed(2)}s
                </div>
            )
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
            const value = row.getValue("ratio") as string
            if (value === null) {
                return (
                    <Skeleton className="h-9 rounded" />
                )
            }
            const numericValue = parseFloat(value)
            const backgroundColor = getTailwindColor(numericValue, max, min)
            return (
                <div className={`${backgroundColor} p-2 rounded text-right font-medium`}>
                    {(numericValue * 100).toFixed(2)}%
                </div>
            )
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
            const value = row.getValue("accuracy") as string
            if (value === null) {
                return (
                    <Skeleton className="h-9 rounded" />
                )
            }
            const numericValue = parseFloat(value)
            const backgroundColor = getTailwindColor(numericValue, min, max)
            return (
                <div className={`${backgroundColor} p-2 rounded text-right font-medium`}>
                    {(numericValue).toFixed(2)}%
                </div>
            )
        }
    },
    {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => {
            const value = row.getValue("status")
            return (
                <>
                    {value === "success" && (
                        <IoCheckmarkCircle className="text-green-400 text-3xl m-auto" />
                    )}
                    {value === "error" && (
                        <IoCloseCircle className="text-red-400 text-3xl m-auto" />
                    )}
                    {value === "pending" && (
                        <IoTime className="text-yellow-400 text-3xl m-auto" />
                    )}
                </>
            )
        },
    }
]