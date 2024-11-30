import { ColumnDef } from "@tanstack/react-table";

export type Result = {
    submission_id: string
    name: string
    submission_name: string
    runtime: number
    ratio: number
    accuracy: number
    status: "pending" | "success" | "failed"
}

export const columns: ColumnDef<Result>[] = [
    {
        accessorKey: "submission_id",
        header: "ID",
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
        header: "Runtime",
    },
    {
        accessorKey: "ratio",
        header: "Deflate Ratio",
    },
    {
        accessorKey: "accuracy",
        header: "Search Accuracy",
    },
    {
        accessorKey: "status",
        header: "Status",
    }
]