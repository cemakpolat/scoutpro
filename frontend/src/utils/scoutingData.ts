export interface MarketValueEstimate {
  estimateMillionEUR?: number;
  displayValue?: string;
  confidence?: number;
  band?: string;
  factors?: Record<string, unknown>;
  player_id?: string;
  player_name?: string;
  position?: string;
}

export interface PlayerScoutingProfile {
  chanceProfile?: Record<string, unknown>;
  ballProgression?: Record<string, unknown>;
  defensivePressure?: Record<string, unknown>;
  setPieceImpact?: Record<string, unknown>;
  developmentCurve?: Record<string, unknown>;
  marketValue?: MarketValueEstimate;
  sample?: Record<string, unknown>;
}

export interface PlayerScoutingPayload {
  player_id?: string;
  player?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  insights?: Array<Record<string, unknown>>;
  scoutingProfile?: PlayerScoutingProfile;
  valuation?: MarketValueEstimate;
  trajectory?: Record<string, unknown>;
  last_updated?: string;
}

type GenericRecord = Record<string, unknown>;

export function toFiniteNumber(value: unknown, fallback = 0): number {
  if (value === null || value === undefined || value === '') {
    return fallback;
  }

  const normalized = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(normalized) ? normalized : fallback;
}

export function parseMarketValueToNumber(value: unknown): number {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value !== 'string') {
    return 0;
  }

  const normalized = value.trim().toLowerCase();
  if (!normalized) {
    return 0;
  }

  const cleaned = normalized.replace(/eur/g, '').replace(/€/g, '').replace(/,/g, '');
  const numericMatch = cleaned.match(/-?\d+(?:\.\d+)?/);
  if (!numericMatch) {
    return 0;
  }

  const baseValue = Number(numericMatch[0]);
  if (!Number.isFinite(baseValue)) {
    return 0;
  }

  if (/\b(bn|billion|b)\b/.test(cleaned)) {
    return baseValue * 1_000_000_000;
  }

  if (/\b(mn|million|m)\b/.test(cleaned)) {
    return baseValue * 1_000_000;
  }

  if (/\b(k|thousand)\b/.test(cleaned)) {
    return baseValue * 1_000;
  }

  return baseValue;
}

export function formatMarketValueCompact(value: unknown): string {
  const numericValue = parseMarketValueToNumber(value);
  if (numericValue > 0) {
    if (numericValue >= 1_000_000_000) {
      return `€${(numericValue / 1_000_000_000).toFixed(1)}B`;
    }

    if (numericValue >= 1_000_000) {
      return `€${(numericValue / 1_000_000).toFixed(1)}M`;
    }

    if (numericValue >= 1_000) {
      return `€${(numericValue / 1_000).toFixed(0)}K`;
    }

    return `€${numericValue.toFixed(0)}`;
  }

  if (typeof value === 'string' && value.trim()) {
    return value.trim();
  }

  return 'N/A';
}

export function resolvePlayerId(player: GenericRecord | null | undefined): string | null {
  if (!player) {
    return null;
  }

  const providerIds = player.provider_ids as GenericRecord | undefined;
  const providerIdsCamel = player.providerIds as GenericRecord | undefined;
  const candidates = [
    player.id,
    player.player_id,
    player.playerId,
    player.scoutpro_id,
    player.uID,
    player.opta_uid,
    providerIds?.opta,
    providerIdsCamel?.opta,
  ];

  for (const candidate of candidates) {
    if (candidate === null || candidate === undefined || candidate === '') {
      continue;
    }

    const normalized = String(candidate).trim();
    if (normalized) {
      return normalized;
    }
  }

  return null;
}

export function resolveContractExpiry(player: GenericRecord | null | undefined): string | null {
  if (!player) {
    return null;
  }

  const contract = player.contract as GenericRecord | string | undefined;
  const directValue = player.contractExpiry
    || player.contract_expiry
    || player.contractEnd
    || player.contract_end;

  if (typeof directValue === 'string' && directValue.trim()) {
    return directValue.trim();
  }

  if (typeof contract === 'string' && contract.trim()) {
    return contract.trim();
  }

  if (contract && typeof contract === 'object') {
    const expiry = contract.expiryDate || contract.endDate || contract.expiry;
    if (typeof expiry === 'string' && expiry.trim()) {
      return expiry.trim();
    }
  }

  return null;
}

export function resolveClubName(player: GenericRecord | null | undefined): string {
  if (!player) {
    return 'Unknown';
  }

  const value = player.club
    || player.team
    || player.team_name
    || player.teamName
    || player.currentClub
    || player.clubName;

  return typeof value === 'string' && value.trim() ? value.trim() : 'Unknown';
}

export function resolvePositionLabel(player: GenericRecord | null | undefined): string {
  if (!player) {
    return 'Unknown';
  }

  const value = player.position
    || player.detailed_position
    || player.detailedPosition
    || player.positionGroup;

  return typeof value === 'string' && value.trim() ? value.trim() : 'Unknown';
}

export function normalizePhaseLabel(value: unknown): string | null {
  if (typeof value !== 'string' || !value.trim()) {
    return null;
  }

  return value
    .trim()
    .split(/[-_\s]+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function resolveScoutingValuation(payload: PlayerScoutingPayload | null | undefined): MarketValueEstimate | null {
  if (!payload) {
    return null;
  }

  return payload.valuation || payload.scoutingProfile?.marketValue || null;
}

export function dedupeByPlayerId<T extends GenericRecord>(players: T[]): T[] {
  const seen = new Set<string>();
  const deduped: T[] = [];

  players.forEach((player) => {
    const playerId = resolvePlayerId(player);
    if (!playerId || seen.has(playerId)) {
      return;
    }

    seen.add(playerId);
    deduped.push(player);
  });

  return deduped;
}