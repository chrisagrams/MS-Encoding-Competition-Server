import { Result, columns } from "./columns"
import { RankingTable } from "./RankingTable"
import { useState, useEffect } from "react"
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"

export const Ranking = () => {

    const [data, setData] = useState<Result[]>([])
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const response = await fetch('/api/results'); 
                
                if (!response.ok) {
                    throw new Error('Failed to get results.');
                }

                const resultData: Result[] = await response.json();
                setData(resultData);
            } catch (err) {
                console.error('Error fetching data:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle>Ranking</CardTitle>
                <CardDescription>Current rankings of submissions.</CardDescription>
            </CardHeader>
            <CardContent>
                <RankingTable columns={columns} data={data} />
            </CardContent>
        </Card>
    )
}