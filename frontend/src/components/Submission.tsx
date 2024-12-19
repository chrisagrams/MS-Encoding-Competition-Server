import { useParams } from "react-router-dom";

export const Submission = () => {
    const { uuid } = useParams(); 
    return (
      <div>
        <h1>Submission Page</h1>
        <p>UUID: {uuid}</p>
      </div>
    );
  }