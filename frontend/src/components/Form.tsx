import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { useState } from "react"
import { useDropzone } from "react-dropzone"
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"

const formSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  name: z
    .string()
    .min(1, { message: "Your name is required" })
    .max(100, { message: "Name must be 100 characters or less" }),
  submissionName: z
    .string()
    .min(1, { message: "Submission name is required" })
    .max(100, { message: "Submission name must be 100 characters or less" }),
  file: z
    .instanceof(File)
    .refine((file) => file.size > 0, { message: "File is required" })
    .refine((file) => file.size <= 25 * 1024 * 1024, { message: "File size must be less than 25MB" })
    .refine((file) => file.type === "application/zip", { message: "File must be a ZIP file" }),
})

export const SubmissionForm = () => {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      submissionName: "",
    },
  })

  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const onDrop = (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    setSelectedFile(file)
    form.setValue("file", file)
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/zip": [".zip"] },
    maxSize: 25 * 1024 * 1024, // 25 MB
  })

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    const formData = new FormData()
    formData.append("email", values.email)
    formData.append("name", values.name)
    formData.append("submissionName", values.submissionName)
    formData.append("file", selectedFile!)

    try {
        const response = await fetch('/api/upload', {
            method: "POST",
            body: formData,
        })

        if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || "Failed to upload")
        }

        const result = await response.json()
        console.log(result)
    }
    catch (error) {
        console.error("Error uploading file: ", error)
    }
  }

  return (
    <Card>
        <CardHeader>
            <CardTitle>Submission</CardTitle>
            <CardDescription>Submit your encoding method.</CardDescription>
        </CardHeader>
        <CardContent>
            <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                    <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                        <Input placeholder="Enter your email" {...field} />
                    </FormControl>
                    <FormDescription>Your email address.</FormDescription>
                    <FormMessage />
                    </FormItem>
                )}
                />
                <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                    <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                        <Input placeholder="Enter your name" {...field} />
                    </FormControl>
                    <FormDescription>Your name will be visible to others.</FormDescription>
                    <FormMessage />
                    </FormItem>
                )}
                />
                <FormField
                control={form.control}
                name="submissionName"
                render={({ field }) => (
                    <FormItem>
                    <FormLabel>Submission Name</FormLabel>
                    <FormControl>
                        <Input placeholder="Enter submission name" {...field} />
                    </FormControl>
                    <FormDescription>A short name for your submission.</FormDescription>
                    <FormMessage />
                    </FormItem>
                )}
                />
                <FormField
                control={form.control}
                name="file"
                render={({ field }) => (
                    <FormItem>
                    <FormLabel>File Upload</FormLabel>
                    <FormControl>
                        <div
                        {...getRootProps()}
                        className={`border-2 border-dashed rounded-md p-4 py-8 cursor-pointer text-center ${
                            isDragActive ? "border-blue-500" : "border-gray-300"
                        }`}
                        >
                        <input {...getInputProps()} />
                        {isDragActive ? (
                            <p>Drop file here...</p>
                        ) : selectedFile ? (
                            <p>{selectedFile.name}</p>
                        ) : (
                            <p>Drag and drop ZIP file here, or click to select one</p>
                        )}
                        </div>
                    </FormControl>
                    <FormDescription>Upload your file. Must be a ZIP and less than 25MB.</FormDescription>
                    <FormMessage />
                    </FormItem>
                )}
                />
                <Button type="submit">Submit</Button>
            </form>
            </Form>
        </CardContent>
    </Card>
  )
}
