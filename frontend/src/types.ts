export type APIErrorDetail = {
    loc?: string[] // (optional) location of error
    msg: string
    type: string
}

export type APIError = {
    detail: string | APIErrorDetail[]
}

export type Result = {
    submission_id: string
    name: string
    submission_name: string
    encoding_runtime: number | null
    decoding_runtime: number | null
    ratio: number | null
    accuracy: number | null
    status: "pending" | "success" | "failed"
    peptide_percent_preserved: number | null
    peptide_percent_missed: number | null
    peptide_percent_new: number | null
}

export type Rank = {
    submission_id: string
    encoding_runtime_rank: number | null
    decoding_runtime_rank: number | null
    ratio_rank: number | null
    accuracy_rank: number | null
    total_entries: number
}