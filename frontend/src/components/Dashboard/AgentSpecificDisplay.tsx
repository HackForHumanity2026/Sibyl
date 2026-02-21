/**
 * AgentSpecificDisplay - Renders agent-specific content based on agent type.
 * Routes to SatelliteImageTile, IFRSCoverageBar, ConsistencyCheckList, or VerdictCard.
 */

import type { AgentSpecificContent } from "@/types/dashboard";
import { SatelliteImageTile } from "./AgentSpecific/SatelliteImageTile";
import { IFRSCoverageBar } from "./AgentSpecific/IFRSCoverageBar";
import { ConsistencyCheckList } from "./AgentSpecific/ConsistencyCheckList";
import { VerdictCard } from "./AgentSpecific/VerdictCard";

interface AgentSpecificDisplayProps {
  content: AgentSpecificContent;
}

export function AgentSpecificDisplay({
  content,
}: AgentSpecificDisplayProps) {
  switch (content.type) {
    case "satellite":
      return (
        <SatelliteImageTile
          imageReferences={content.imageReferences}
          location={content.location}
          imageryDate={content.imageryDate}
          beforeDate={content.beforeDate}
          ndviValues={content.ndviValues}
        />
      );

    case "ifrs_coverage":
      return <IFRSCoverageBar coverage={content.coverage} />;

    case "consistency_checks":
      return <ConsistencyCheckList checks={content.checks} />;

    case "verdicts":
      return <VerdictCard verdicts={content.verdicts} />;

    default: {
      const _exhaustiveCheck: never = content;
      console.warn("Unhandled agent-specific content type:", _exhaustiveCheck);
      return null;
    }
  }
}
