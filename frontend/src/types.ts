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
    encoding_runtime: number
    decoding_runtime: number
    ratio: number
    accuracy: number
    status: "pending" | "success" | "failed"
    peptide_percent_preserved: number
    peptide_percent_missed: number
    peptide_percent_new: number
}

export type Rank = {
    submission_id: string
    encoding_runtime_rank: number
    decoding_runtime_rank: number
    ratio_rank: number
    accuracy_rank: number
    total_entries: number
}