import { Result, columns } from "./columns"
import { RankingTable } from "./RankingTable"
import { useState, useEffect } from "react"

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
        <div className="container mx-auto py-10">
            <RankingTable columns={columns} data={data} />
        </div>
    )
}