import { PieChart, Pie, Tooltip } from "recharts";
import {
  ChartContainer,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { Result } from "@/types";
import colors from "tailwindcss/colors";


const chartConfig = {
  preserved: {
    label: "Preserved",
    color: colors.green[400],
  },
  missed: {
    label: "Missed",
    color: colors.red[400],
  },
  new: {
    label: "New",
    color: colors.purple[400],
  },
} satisfies ChartConfig;

type IdentificationChartProps = {
  data: Result | undefined;
};

export const IdentificationChart: React.FC<IdentificationChartProps> = ({ data }) => {
  const pieData = [
    {
      name: "Preserved",
      value: data?.peptide_percent_preserved,
      fill: chartConfig.preserved.color,
      label: `${chartConfig.preserved.label} (${data?.peptide_percent_preserved?.toFixed(2)}%)`,
    },
    {
      name: "Missed",
      value: data?.peptide_percent_missed,
      fill: chartConfig.missed.color,
      label: `${chartConfig.missed.label} (${data?.peptide_percent_missed?.toFixed(2)}%)`,
    },
    {
      name: "New",
      value: data?.peptide_percent_new,
      fill: chartConfig.new.color,
      label: `${chartConfig.new.label} (${data?.peptide_percent_new?.toFixed(2)}%)`,
    },
  ];

  return (
    <ChartContainer config={chartConfig}>
      <PieChart accessibilityLayer>
        <Pie
          data={pieData}
          dataKey="value"
          nameKey="name"
          label={({ name, value }) =>
            `${name} (${value?.toFixed(2)}%)`
          }
          paddingAngle={2.5} minAngle={2.5}
        />
        <Tooltip content={<ChartTooltipContent />} />
      </PieChart>
    </ChartContainer>
  );
};
