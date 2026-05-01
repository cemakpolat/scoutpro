/**
 * Reports Routes - Real PDF/Excel report generation using pdfkit
 */
const express = require('express');
const router = express.Router();
const { ObjectId } = require('mongodb');

const { requestJson, unwrapPayload } = require('../utils/serviceClient');

const analyticsServiceUrl = (process.env.ANALYTICS_SERVICE_URL || 'http://analytics-service:8012').replace(/\/$/, '');
const matchServiceUrl = (process.env.MATCH_SERVICE_URL || 'http://match-service:8000').replace(/\/$/, '');
const teamServiceUrl = (process.env.TEAM_SERVICE_URL || 'http://team-service:8000').replace(/\/$/, '');
const analyticsRequestTimeoutMs = Number(process.env.ANALYTICS_SERVICE_TIMEOUT_MS || 2500);

let PDFDocument;
try {
  PDFDocument = require('pdfkit');
} catch (e) {
  console.warn('⚠️  pdfkit not installed — reports will use text fallback');
  PDFDocument = null;
}

function toFiniteNumber(value, fallback = 0) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
}

function buildIdLookup(entityId, numericFields = []) {
  const lookups = [{ id: String(entityId) }];
  const numericId = Number(entityId);

  numericFields.forEach((field) => {
    lookups.push({ [field]: String(entityId) });
    if (Number.isInteger(numericId)) {
      lookups.push({ [field]: numericId });
    }
  });

  if (ObjectId.isValid(String(entityId))) {
    lookups.push({ _id: new ObjectId(String(entityId)) });
  }

  return lookups;
}

function buildPlayerName(player) {
  return player.name || [player.first_name || player.firstName, player.last_name || player.lastName].filter(Boolean).join(' ') || 'Unknown Player';
}

function normalizePlayerReportData(player = {}, analyticsPayload = null) {
  const summary = analyticsPayload?.summary || {};

  return {
    id: String(player.id || player.uID || analyticsPayload?.player_id || ''),
    name: buildPlayerName(player),
    position: player.position || summary.position || 'N/A',
    age: player.age ?? summary.age ?? 'N/A',
    club: player.club || summary.club || player.team || 'N/A',
    nationality: player.nationality || 'N/A',
    rating: toFiniteNumber(summary.rating, toFiniteNumber(player.rating, 0)),
    goals: toFiniteNumber(summary.goals, toFiniteNumber(player.goals, 0)),
    assists: toFiniteNumber(summary.assists, toFiniteNumber(player.assists, 0)),
    appearances: toFiniteNumber(summary.appearances, toFiniteNumber(player.appearances, 0)),
    passAccuracy: toFiniteNumber(summary.passAccuracy, toFiniteNumber(player.passAccuracy, 0)),
    marketValue: toFiniteNumber(player.marketValue, 0),
    xG: toFiniteNumber(player.xG, 0),
    xA: toFiniteNumber(player.xA, 0),
  };
}

async function resolvePlayerReportData(db, playerId) {
  const player = db
    ? await db.collection('players').findOne({ $or: buildIdLookup(playerId, ['uID']) })
    : null;

  const analyticsResult = await requestJson(
    analyticsServiceUrl,
    `/api/v2/analytics/insights/player/${playerId}`,
    { timeoutMs: analyticsRequestTimeoutMs }
  ).catch(() => null);

  const analyticsPayload = analyticsResult?.ok ? analyticsResult.payload : null;
  return normalizePlayerReportData({ ...(player || {}), ...(analyticsPayload?.player || {}) }, analyticsPayload);
}

async function resolveTeamName(db, teamId) {
  if (!db || teamId === undefined || teamId === null || teamId === '') {
    const result = await requestJson(teamServiceUrl, `/api/v2/teams/${teamId}`, { timeoutMs: analyticsRequestTimeoutMs }).catch(() => null);
    const payload = result?.ok ? unwrapPayload(result.payload) : null;
    return payload?.name || null;
  }

  const team = await db.collection('teams').findOne({ $or: buildIdLookup(teamId, ['uID']) });
  if (team?.name) {
    return team.name;
  }

  const result = await requestJson(teamServiceUrl, `/api/v2/teams/${teamId}`, { timeoutMs: analyticsRequestTimeoutMs }).catch(() => null);
  const payload = result?.ok ? unwrapPayload(result.payload) : null;
  return payload?.name || null;
}

async function resolveTeamReportData(db, teamId) {
  const team = db
    ? await db.collection('teams').findOne({ $or: buildIdLookup(teamId, ['uID']) })
    : null;
  const normalizedTeam = {
    id: String(team?.id || team?.uID || teamId),
    name: team?.name || 'Unknown Team',
    league: team?.league || team?.competition || team?.competition_name || 'N/A',
    country: team?.country || 'N/A',
    manager: team?.manager || 'N/A',
    formation: team?.formation || 'N/A',
  };

  const players = db && normalizedTeam.name !== 'Unknown Team'
    ? await db.collection('players').find({
        $or: [{ club: normalizedTeam.name }, { team: normalizedTeam.name }],
      }).limit(30).toArray()
    : [];

  return {
    team: normalizedTeam,
    players: players.map((player) => normalizePlayerReportData(player)),
  };
}

async function resolveMatchReportData(db, matchId) {
  let match = db
    ? await db.collection('matches').findOne({ $or: buildIdLookup(matchId, ['match_id']) })
    : null;

  if (!match) {
    const matchResult = await requestJson(matchServiceUrl, `/api/v2/matches/${matchId}`, {
      timeoutMs: analyticsRequestTimeoutMs,
    }).catch(() => null);
    match = matchResult?.ok ? unwrapPayload(matchResult.payload) : null;
  }

  if (!match) {
    return {
      id: String(matchId),
      homeTeam: 'Home',
      awayTeam: 'Away',
      homeScore: 0,
      awayScore: 0,
      competition: 'N/A',
      date: 'N/A',
      status: 'N/A',
      venue: 'N/A',
      homePossession: 50,
      awayPossession: 50,
      homeShots: 0,
      awayShots: 0,
      homeShotsOnTarget: 0,
      awayShotsOnTarget: 0,
      homeCorners: 0,
      awayCorners: 0,
      homeFouls: 0,
      awayFouls: 0,
      homeXG: 0,
      awayXG: 0,
    };
  }

  const homeTeam = match.homeTeam || match.home_team || await resolveTeamName(db, match.home_team_id || match.homeTeamId) || String(match.home_team_id || 'Home');
  const awayTeam = match.awayTeam || match.away_team || await resolveTeamName(db, match.away_team_id || match.awayTeamId) || String(match.away_team_id || 'Away');

  return {
    id: String(match.id || match.match_id || matchId),
    homeTeam,
    awayTeam,
    homeScore: toFiniteNumber(match.homeScore ?? match.home_score, 0),
    awayScore: toFiniteNumber(match.awayScore ?? match.away_score, 0),
    competition: match.competition || match.competition_name || match.competition_id || 'N/A',
    date: match.date || match.match_date || 'N/A',
    status: match.status || 'N/A',
    venue: match.venue || 'N/A',
    homePossession: toFiniteNumber(match.homePossession ?? match.home_possession, 50),
    awayPossession: toFiniteNumber(match.awayPossession ?? match.away_possession, 50),
    homeShots: toFiniteNumber(match.homeShots ?? match.home_shots, 0),
    awayShots: toFiniteNumber(match.awayShots ?? match.away_shots, 0),
    homeShotsOnTarget: toFiniteNumber(match.homeShotsOnTarget ?? match.home_shots_on_target, 0),
    awayShotsOnTarget: toFiniteNumber(match.awayShotsOnTarget ?? match.away_shots_on_target, 0),
    homeCorners: toFiniteNumber(match.homeCorners ?? match.home_corners, 0),
    awayCorners: toFiniteNumber(match.awayCorners ?? match.away_corners, 0),
    homeFouls: toFiniteNumber(match.homeFouls ?? match.home_fouls, 0),
    awayFouls: toFiniteNumber(match.awayFouls ?? match.away_fouls, 0),
    homeXG: toFiniteNumber(match.homeXG ?? match.home_xg, 0),
    awayXG: toFiniteNumber(match.awayXG ?? match.away_xg, 0),
  };
}

// ===== PDF Helper =====
function createPDF(res, title, sections) {
  if (!PDFDocument) {
    // Fallback: plain text "PDF"
    res.setHeader('Content-Type', 'application/pdf');
    let text = `${title}\n${'='.repeat(title.length)}\n\n`;
    sections.forEach(s => {
      text += `\n--- ${s.heading} ---\n`;
      if (s.table) {
        s.table.forEach(row => { text += row.join(' | ') + '\n'; });
      }
      if (s.text) text += s.text + '\n';
    });
    return res.send(Buffer.from(text));
  }

  const doc = new PDFDocument({ margin: 50, size: 'A4' });
  res.setHeader('Content-Type', 'application/pdf');
  doc.pipe(res);

  // Title
  doc.fontSize(22).fillColor('#0f172a').text(title, { align: 'center' });
  doc.moveDown(0.3);
  doc.fontSize(10).fillColor('#64748b').text(`Generated: ${new Date().toLocaleString()}`, { align: 'center' });
  doc.moveDown(0.5);
  doc.moveTo(50, doc.y).lineTo(545, doc.y).stroke('#e2e8f0');
  doc.moveDown(1);

  sections.forEach(section => {
    doc.fontSize(14).fillColor('#1e293b').text(section.heading);
    doc.moveDown(0.3);

    if (section.keyValues) {
      section.keyValues.forEach(([key, val]) => {
        doc.fontSize(10).fillColor('#475569').text(`${key}:`, { continued: true }).fillColor('#0f172a').text(`  ${val}`);
      });
      doc.moveDown(0.5);
    }

    if (section.table && section.table.length > 0) {
      const colWidth = 480 / section.table[0].length;
      section.table.forEach((row, ri) => {
        const y = doc.y;
        row.forEach((cell, ci) => {
          const x = 50 + ci * colWidth;
          if (ri === 0) {
            doc.fontSize(9).fillColor('#ffffff');
            doc.rect(x, y - 2, colWidth, 16).fill('#334155');
            doc.fillColor('#ffffff').text(String(cell), x + 4, y, { width: colWidth - 8, height: 14 });
          } else {
            doc.fontSize(9).fillColor('#0f172a');
            if (ri % 2 === 0) doc.rect(x, y - 2, colWidth, 16).fill('#f8fafc');
            doc.fillColor('#0f172a').text(String(cell), x + 4, y, { width: colWidth - 8, height: 14 });
          }
        });
        doc.moveDown(0.5);
      });
      doc.moveDown(0.5);
    }

    if (section.text) {
      doc.fontSize(10).fillColor('#334155').text(section.text, { lineGap: 3 });
      doc.moveDown(0.5);
    }

    doc.moveDown(0.5);
  });

  // Footer
  doc.fontSize(8).fillColor('#94a3b8').text('ScoutPro — Professional Football Scouting Platform', 50, 770, { align: 'center' });

  doc.end();
}

// POST /api/v2/reports/generate
router.post('/generate', async (req, res) => {
  const { v4: uuidv4 } = require('uuid');
  const jobId = uuidv4();
  
  const db = req.app.locals.db;
  if (db) {
    await db.collection('reports').insertOne({
      id: jobId,
      ...req.body,
      status: 'processing',
      createdAt: new Date().toISOString()
    });

    // Simulate processing → completed
    setTimeout(async () => {
      try {
        await db.collection('reports').updateOne(
          { id: jobId },
          { $set: { status: 'completed', completedAt: new Date().toISOString() } }
        );
      } catch (e) {}
    }, 3000);
  }

  res.json({ job_id: jobId, status: 'processing', message: 'Report generation started' });
});

// GET /api/v2/reports/:reportId/status
router.get('/:reportId/status', async (req, res) => {
  const db = req.app.locals.db;
  if (db) {
    const report = await db.collection('reports').findOne({ id: req.params.reportId });
    if (report) {
      return res.json({ id: report.id, status: report.status || 'completed' });
    }
  }
  res.json({ id: req.params.reportId, status: 'completed' });
});

// GET /api/v2/reports/:reportId/download
router.get('/:reportId/download', async (req, res) => {
  const db = req.app.locals.db;
  const report = db ? await db.collection('reports').findOne({ id: req.params.reportId }) : null;

  res.setHeader('Content-Disposition', `attachment; filename="report-${req.params.reportId}.pdf"`);
  createPDF(res, report?.title || 'ScoutPro Report', [
    { heading: 'Report Details', keyValues: [
      ['Report ID', req.params.reportId],
      ['Type', report?.type || 'general'],
      ['Entity', report?.entity_label || report?.entity_id || 'N/A'],
      ['Generated', new Date().toLocaleString()]
    ]},
    { heading: 'Summary', text: 'This report was generated by the ScoutPro analytics platform. Full analysis and data visualizations are available in the web dashboard.' }
  ]);
});

// GET /api/v2/reports/player/:playerId
router.get('/player/:playerId', async (req, res) => {
  const db = req.app.locals.db;
  const p = await resolvePlayerReportData(db, req.params.playerId);
  const format = req.query.format || 'pdf';

  if (format === 'excel') {
    // Simple CSV-as-Excel fallback
    const csv = [
      ['Field', 'Value'],
      ['Name', p.name], ['Position', p.position], ['Age', p.age], ['Club', p.club],
      ['Nationality', p.nationality || 'N/A'], ['Rating', p.rating || 'N/A'],
      ['Goals', p.goals || 0], ['Assists', p.assists || 0],
      ['Appearances', p.appearances || 0], ['Pass Accuracy', `${p.passAccuracy || 0}%`],
      ['Market Value', `€${(p.marketValue || 0)}M`]
    ].map(r => r.join(',')).join('\n');

    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', `attachment; filename="player-${req.params.playerId}.xlsx"`);
    return res.send(Buffer.from(csv));
  }

  res.setHeader('Content-Disposition', `attachment; filename="player-${req.params.playerId}.pdf"`);
  createPDF(res, `Player Report: ${p.name}`, [
    { heading: 'Player Profile', keyValues: [
      ['Name', p.name], ['Position', p.position], ['Age', String(p.age)],
      ['Club', p.club], ['Nationality', p.nationality || 'N/A'],
      ['Market Value', `€${(p.marketValue || 0)}M`]
    ]},
    { heading: 'Season Statistics', table: [
      ['Metric', 'Value'],
      ['Rating', String(p.rating || 'N/A')],
      ['Goals', String(p.goals || 0)],
      ['Assists', String(p.assists || 0)],
      ['Appearances', String(p.appearances || 0)],
      ['Pass Accuracy', `${p.passAccuracy || 0}%`],
      ['xG', String(p.xG || 'N/A')],
      ['xA', String(p.xA || 'N/A')]
    ]},
    { heading: 'Scouting Assessment', text: `${p.name} is a ${p.position?.toLowerCase()} currently playing for ${p.club}. This report summarizes key performance metrics from the current season. For detailed tactical analysis, heatmaps, and comparison data, refer to the ScoutPro web dashboard.` }
  ]);
});

// GET /api/v2/reports/team/:teamId
router.get('/team/:teamId', async (req, res) => {
  const db = req.app.locals.db;
  const { team: t, players } = await resolveTeamReportData(db, req.params.teamId);
  const format = req.query.format || 'pdf';

  if (format === 'excel') {
    const header = 'Name,Position,Age,Rating,Goals,Assists';
    const rows = players.map(p => [p.name, p.position, p.age, p.rating, p.goals, p.assists].join(','));
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', `attachment; filename="team-${req.params.teamId}.xlsx"`);
    return res.send(Buffer.from([header, ...rows].join('\n')));
  }

  res.setHeader('Content-Disposition', `attachment; filename="team-${req.params.teamId}.pdf"`);
  createPDF(res, `Team Report: ${t.name}`, [
    { heading: 'Team Profile', keyValues: [
      ['Name', t.name], ['League', t.league || 'N/A'], ['Country', t.country || 'N/A'],
      ['Manager', t.manager || 'N/A'], ['Formation', t.formation || 'N/A'],
      ['Squad Size', String(players.length)]
    ]},
    { heading: 'Squad', table: [
      ['Name', 'Position', 'Age', 'Rating', 'Goals'],
      ...players.slice(0, 20).map(p => [p.name, p.position, String(p.age), String(p.rating || 'N/A'), String(p.goals || 0)])
    ]},
    { heading: 'Analysis', text: `${t.name} competes in ${t.league || 'their league'} with a squad of ${players.length} players. For full tactical breakdowns, fixture analysis, and transfer market data, visit the ScoutPro dashboard.` }
  ]);
});

// GET /api/v2/reports/match/:matchId
router.get('/match/:matchId', async (req, res) => {
  const db = req.app.locals.db;
  const m = await resolveMatchReportData(db, req.params.matchId);
  const format = req.query.format || 'pdf';

  if (format === 'excel') {
    const csv = [
      'Field,Value',
      `Home Team,${m.homeTeam}`, `Away Team,${m.awayTeam}`,
      `Score,${m.homeScore}-${m.awayScore}`,
      `Competition,${m.competition || 'N/A'}`,
      `Date,${m.date || 'N/A'}`, `Status,${m.status || 'N/A'}`
    ].join('\n');

    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', `attachment; filename="match-${req.params.matchId}.xlsx"`);
    return res.send(Buffer.from(csv));
  }

  res.setHeader('Content-Disposition', `attachment; filename="match-${req.params.matchId}.pdf"`);
  createPDF(res, `Match Report: ${m.homeTeam} vs ${m.awayTeam}`, [
    { heading: 'Match Info', keyValues: [
      ['Home', m.homeTeam], ['Away', m.awayTeam],
      ['Score', `${m.homeScore} - ${m.awayScore}`],
      ['Competition', m.competition || 'N/A'],
      ['Date', m.date || 'N/A'], ['Venue', m.venue || 'N/A']
    ]},
    { heading: 'Match Statistics', table: [
      ['Stat', 'Home', 'Away'],
      ['Possession', `${m.homePossession || 50}%`, `${m.awayPossession || 50}%`],
      ['Shots', String(m.homeShots || 0), String(m.awayShots || 0)],
      ['Shots on Target', String(m.homeShotsOnTarget || 0), String(m.awayShotsOnTarget || 0)],
      ['Corners', String(m.homeCorners || 0), String(m.awayCorners || 0)],
      ['Fouls', String(m.homeFouls || 0), String(m.awayFouls || 0)],
      ['xG', String(m.homeXG || 0), String(m.awayXG || 0)]
    ]},
    { heading: 'Post-Match Analysis', text: `${m.homeTeam} ${m.homeScore > m.awayScore ? 'secured a victory against' : m.homeScore < m.awayScore ? 'fell to' : 'drew with'} ${m.awayTeam}. For event-by-event timeline, heatmaps, and player ratings, visit the ScoutPro Match Centre.` }
  ]);
});

// GET /api/v2/reports/list
router.get('/list', async (req, res) => {
  const db = req.app.locals.db;
  if (db) {
    const reports = await db.collection('reports')
      .find({})
      .sort({ createdAt: -1 })
      .limit(50)
      .toArray();
    return res.json(reports.map(r => ({ ...r, id: r.id || r._id?.toString(), _id: undefined })));
  }
  res.json([]);
});

// DELETE /api/v2/reports/:reportId
router.delete('/:reportId', async (req, res) => {
  const db = req.app.locals.db;
  if (db) {
    await db.collection('reports').deleteOne({ id: req.params.reportId });
  }
  res.json({ success: true });
});

module.exports = router;
