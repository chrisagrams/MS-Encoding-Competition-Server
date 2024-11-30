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

const computeMinMax = (rows: any[], columnId: string) => {
    const values = rows.map((row) => parseFloat(row.getValue(columnId)));
    return {
      min: Math.min(...values),
      max: Math.max(...values),
    };
};

const getColor = (value: number, min: number, max: number) => {
    const ratio = (value - min) / (max - min);
    const red = Math.round(255 * ratio);
    const green = Math.round(255 * (1 - ratio));
    const blue = 50;
    return `rgb(${red}, ${green}, ${blue})`;
};

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
        cell: ({ row, table }) => {
            const { min, max } = computeMinMax(table.getRowModel().rows, "runtime")
            const value = parseFloat(row.getValue("runtime"))
            const backgroundColor = getColor(value, min, max)
            return (
                <div
                  style={{
                    backgroundColor,
                    padding: "8px",
                    borderRadius: "4px",
                    textAlign: "right",
                    fontWeight: "500",
                  }}
                >
                  {value}s
                </div>
              );
        }
    },
    {
        accessorKey: "ratio",
        header: "Deflate Ratio",
        cell: ({ row, table }) => {
            const { min, max } = computeMinMax(table.getRowModel().rows, "ratio")
            const value = parseFloat(row.getValue("ratio"))
            const backgroundColor = getColor(value, max, min)
            return (
                <div
                  style={{
                    backgroundColor,
                    padding: "8px",
                    borderRadius: "4px",
                    textAlign: "right",
                    fontWeight: "500",
                  }}
                >
                  {(value * 100).toFixed(2)}%
                </div>
              );
        }
    },
    {
        accessorKey: "accuracy",
        header: "Search Accuracy",
        cell: ({ row, table }) => {
            const { min, max } = computeMinMax(table.getRowModel().rows, "accuracy")
            const value = parseFloat(row.getValue("accuracy"))
            const backgroundColor = getColor(value, max, min)
            return (
                <div
                  style={{
                    backgroundColor,
                    padding: "8px",
                    borderRadius: "4px",
                    textAlign: "right",
                    fontWeight: "500",
                  }}
                >
                  {(value * 100).toFixed(2)}%
                </div>
              );
        }
    },
    {
        accessorKey: "status",
        header: "Status",
    }
]