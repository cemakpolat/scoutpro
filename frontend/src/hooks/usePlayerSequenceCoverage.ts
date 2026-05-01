import { useEffect, useMemo, useState } from 'react';
import apiService from '../services/api';

export function usePlayerSequenceCoverage(playerIds: Array<string | number | null | undefined>) {
  const normalizedPlayerIds = useMemo(
    () => Array.from(new Set(
      playerIds
        .map((playerId) => String(playerId ?? '').trim())
        .filter((playerId) => playerId && playerId !== 'null' && playerId !== 'undefined')
    )),
    [playerIds]
  );

  const [coverageByPlayerId, setCoverageByPlayerId] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;

    if (normalizedPlayerIds.length === 0) {
      setCoverageByPlayerId({});
      setLoading(false);
      return () => {
        active = false;
      };
    }

    setLoading(true);

    void apiService.getPlayerSequenceCoverage(normalizedPlayerIds).then((response) => {
      if (!active) {
        return;
      }

      const nextCoverageByPlayerId: Record<string, any> = {};
      const items = response.success ? response.data?.items || [] : [];
      items.forEach((item: any) => {
        if (item?.player_id) {
          nextCoverageByPlayerId[String(item.player_id)] = item;
        }
      });
      setCoverageByPlayerId(nextCoverageByPlayerId);
    }).finally(() => {
      if (active) {
        setLoading(false);
      }
    });

    return () => {
      active = false;
    };
  }, [normalizedPlayerIds.join('|')]);

  const sequenceReadyCount = useMemo(
    () => Object.values(coverageByPlayerId).filter((coverage: any) => coverage?.hasCoverage === true).length,
    [coverageByPlayerId]
  );

  return {
    coverageByPlayerId,
    loading,
    sequenceReadyCount,
  };
}