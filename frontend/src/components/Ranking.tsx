import { columns } from "./columns"
import { Result } from "@/types";
import { RankingTable } from "./RankingTable"
import { useState, useEffect } from "react"
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"

export const Ranking = () => {

    const [data, setData] = useState<Result[]>([])
    // const [loading, setLoading] = useState<boolean>(true); //TODO: Show loading spinner

    useEffect(() => {
        const fetchData = async () => {
            try {
                // setLoading(true);
                const response = await fetch('/api/results'); 
                
                if (!response.ok) {
                    throw new Error('Failed to get results.');
                }

                const resultData: Result[] = await response.json();
                setData(resultData);
            } catch (err) {
                console.error('Error fetching data:', err);
            } finally {
                // setLoading(false);
            }
        };
        fetchData();
        const intervalId = setInterval(fetchData, 1000);
        return () => clearInterval(intervalId);
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