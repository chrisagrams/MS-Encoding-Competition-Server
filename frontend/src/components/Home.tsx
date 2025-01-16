import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import github from "@/assets/github.svg";

export const Home = () => {
  const navigate = useNavigate();

  return (
    <>
      <Card className="h-full">
        <CardHeader>
          <CardTitle>MS Encoding Competition</CardTitle>
          <CardDescription>
            A competition set out to determine the best encoding/decoding
            methods for mass spectrometry data.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            onClick={() =>
              window.open(
                "https://github.com/chrisagrams/MS-Encoding-Competition",
                "_blank",
                "noopener,noreferrer"
              )
            }
          >
            <img className="w-4" src={github}></img>
            Code Repository
          </Button>
          <hr className="my-4"></hr>
          <div className="flex gap-4">
            <Button
              onClick={() => {
                navigate("/submit");
              }}
            >
              Make a Submission
            </Button>
            <Button
              onClick={() => {
                navigate("/ranking");
              }}
            >
              View Rankings
            </Button>
          </div>
        </CardContent>
        <CardFooter></CardFooter>
      </Card>
    </>
  );
};
