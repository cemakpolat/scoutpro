import { expect, test, type APIRequestContext, type Locator } from '@playwright/test';

import { openTab, seedAuthenticatedSession } from './helpers/auth';

async function selectSecondOptionIfAvailable(locator: Locator) {
  const optionCount = await locator.locator('option').count();
  if (optionCount < 2) {
    return;
  }

  const secondValue = await locator.locator('option').nth(1).getAttribute('value');
  if (secondValue) {
    await locator.selectOption(secondValue);
  }
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function unwrapPayload<T = any>(payload: any): T {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return payload.data as T;
  }

  return payload as T;
}

function pickArray(payload: any, keys: string[] = []): any[] {
  const unwrapped = unwrapPayload(payload);

  if (Array.isArray(unwrapped)) {
    return unwrapped;
  }

  if (!unwrapped || typeof unwrapped !== 'object') {
    return [];
  }

  for (const key of keys) {
    if (Array.isArray(unwrapped[key])) {
      return unwrapped[key];
    }
  }

  return [];
}

function getEntityId(entity: any): string | undefined {
  const value = entity?.id ?? entity?._id ?? entity?.uID;
  return value == null ? undefined : String(value);
}

async function getPlayers(request: APIRequestContext, limit = 6) {
  const response = await request.get(`/api/players?limit=${limit}`);
  expect(response.ok()).toBeTruthy();

  const payload = await response.json();
  return pickArray(payload, ['players']).filter((player) => typeof player?.name === 'string');
}

async function deleteCollaborationEntities(
  request: APIRequestContext,
  workspaceName: string,
  taskTitle: string,
) {
  try {
    const response = await request.get('/api/v2/collaboration');
    if (!response.ok()) {
      return;
    }

    const payload = unwrapPayload(await response.json()) as {
      workspaces?: any[];
      tasks?: any[];
    };

    const task = (payload.tasks || []).find((item) => item?.title === taskTitle);
    const workspace = (payload.workspaces || []).find((item) => item?.name === workspaceName);

    const taskId = getEntityId(task);
    if (taskId) {
      await request.delete(`/api/v2/collaboration/tasks/${taskId}`);
    }

    const workspaceId = getEntityId(workspace);
    if (workspaceId) {
      await request.delete(`/api/v2/collaboration/workspaces/${workspaceId}`);
    }
  } catch {
    // Cleanup should not mask the originating browser failure.
  }
}

async function deleteCalendarEventByTitle(request: APIRequestContext, eventTitle: string) {
  try {
    const response = await request.get('/api/v2/calendar');
    if (!response.ok()) {
      return;
    }

    const payload = unwrapPayload(await response.json()) as {
      events?: any[];
    };

    const event = (payload.events || []).find((item) => item?.title === eventTitle);
    const eventId = getEntityId(event);

    if (eventId) {
      await request.delete(`/api/v2/calendar/events/${eventId}`);
    }
  } catch {
    // Cleanup should not mask the originating browser failure.
  }
}

test.describe('stabilized frontend flows', () => {
  test('report builder supports direct export and queued job cleanup', async ({ page }) => {
    await seedAuthenticatedSession(page, 'scout');
    await page.goto('/');

    await openTab(page, 'Report Builder');
    await expect(page.getByRole('heading', { name: 'Report Builder', level: 1 })).toBeVisible();

    const uniqueTitle = `Playwright Market Report ${Date.now()}`;
    await page.locator('main input[type="text"]').fill(uniqueTitle);

    const selects = page.locator('main select');
    await selects.nth(0).selectOption({ index: 1 });
    await page.locator('main button:has-text("Download PDF")').first().click();
    await expect(page.locator('main')).toContainText('PDF downloaded for');

    await page.getByText('Market Intelligence', { exact: true }).click();
    await expect(page.locator('main button:has-text("Queue PDF")').first()).toBeVisible();
    await page.locator('main input[type="text"]').fill(uniqueTitle);
    await page.locator('main button:has-text("Queue Backend Job")').first().click();
    await expect(page.locator('main')).toContainText(`started for Global market overview`, { timeout: 15000 });
    await expect(page.locator('main')).toContainText(uniqueTitle, { timeout: 15000 });

    const recentReportCards = page.locator('main button:has-text("Delete")');
    await recentReportCards.first().click();
    await expect(page.locator('main')).toContainText('Deleted backend report', { timeout: 15000 });
    await expect(page.getByText(uniqueTitle, { exact: true })).toHaveCount(1);
  });

  test('admin console renders backend-backed sections for admin role', async ({ page }) => {
    await seedAuthenticatedSession(page, 'admin');
    await page.goto('/');

    await openTab(page, 'Admin Console');
    await expect(page.getByRole('heading', { name: 'Admin Console', level: 1 })).toBeVisible();
    await expect(page.locator('main')).toContainText('System Healthy');

    await page.getByRole('button', { name: 'Permissions' }).click();
    await expect(page.locator('main')).toContainText('Role-Based Access Control');
    await expect(page.locator('main')).toContainText('Permission Matrix');

    await page.getByRole('button', { name: 'API Keys' }).click();
    await expect(page.locator('main')).toContainText('API Key Management');
    await expect(page.locator('main')).toContainText('Mobile App');

    await page.getByRole('button', { name: 'Audit Logs' }).click();
    await expect(page.locator('main')).toContainText('Audit Trail');
    await expect(page.locator('main')).toContainText('Generated backend report');

    await page.getByRole('button', { name: 'Subscriptions' }).click();
    await expect(page.locator('main')).toContainText('Subscription Management');
    await expect(page.locator('main')).toContainText('ScoutPro Demo FC');

    await page.getByRole('button', { name: 'System Health' }).click();
    await expect(page.locator('main')).toContainText('System Alerts');

    await page.getByRole('button', { name: 'Refresh' }).click();
    await expect(page.locator('main')).toContainText('Reports Pipeline');
  });

  test('performance tracker renders live metrics and player-derived insights', async ({ page }) => {
    await seedAuthenticatedSession(page, 'scout');
    await page.goto('/');

    await openTab(page, 'Performance Tracker');
    await expect(page.getByRole('heading', { name: 'Performance Tracker', level: 1 })).toBeVisible();
    await expect(page.locator('main')).toContainText('Overall Rating');
    await expect(page.locator('main')).toContainText('Efficiency');
    await expect(page.locator('main')).toContainText('Injury Risk');
    await expect(page.locator('main')).toContainText('Development Tracking');
    await expect(page.locator('main')).toContainText('Injury Risk Analysis');
    await expect(page.locator('main')).toContainText('performance metrics trending upward');

    const mainText = await page.locator('main').innerText();
    expect(mainText).toMatch(/Overall Rating/);
    expect(mainText).toMatch(/\b\d+\.\d\b/);
    expect(mainText).toMatch(/\d+%/);
    expect(mainText).toContain('performance metrics trending upward');
  });

  test('match centre renders live context and supports match switching', async ({ page }) => {
    await seedAuthenticatedSession(page, 'scout');
    await page.goto('/');

    await openTab(page, 'Match Centre');
    await expect(page.getByRole('heading', { name: 'Match Centre', level: 1 })).toBeVisible();
    await expect(page.locator('main')).toContainText('Live Event Stream');
    await expect(page.locator('main')).toContainText('AI Commentary & Insights');
    await expect(page.locator('main')).toContainText('Live Win Probability');
    await expect(page.locator('main')).toContainText('Live Statistics');
    await expect(page.locator('main')).toContainText('Sequence Pressure Snapshot');
    await expect(page.locator('main')).toContainText('Rapid Regains / Second Balls');

    const matchSelect = page.locator('main select').first();
    await expect(matchSelect).toBeVisible();
    expect(await matchSelect.locator('option').count()).toBeGreaterThan(0);
    await selectSecondOptionIfAvailable(matchSelect);

    const mainText = await page.locator('main').innerText();
    expect(mainText).toMatch(/LIVE|PAUSED/);
    expect(mainText).toMatch(/Possession/);
  });

  test('tactical analyzer exposes live sequence intelligence and parameter switching', async ({ page }) => {
    await seedAuthenticatedSession(page, 'scout');
    await page.goto('/');

    await openTab(page, 'Tactical Analyzer');
    await expect(page.getByRole('heading', { name: 'Tactical Analyzer', level: 1 })).toBeVisible();
    await expect(page.locator('main')).toContainText('Formation Analysis');
    await expect(page.locator('main')).toContainText('Live Sequence Intelligence');
    await expect(page.locator('main')).toContainText('Top Live Sequences');

    const selects = page.locator('main select');
    const selectCount = await selects.count();
    if (selectCount > 1) {
      await selectSecondOptionIfAvailable(selects.first());
      await selects.nth(1).selectOption('historical');
    }

    await page.getByRole('button', { name: '4-2-3-1' }).click();
    await page.getByRole('button', { name: 'Defense' }).click();
    await expect(page.locator('main')).toContainText('Advanced Tactical Analytics');

    const tacticalText = await page.locator('main').innerText();
    expect(tacticalText).toMatch(/Providers:/);
    expect(tacticalText).toMatch(/Direct Attacks|Final-Third Entries/);
  });

  test('video analysis supports browser video creation and annotation workflow', async ({ page, request }) => {
    await seedAuthenticatedSession(page, 'scout');
    await page.goto('/');

    const uniqueTitle = `Playwright Video ${Date.now()}`;
    const annotationText = `Automated note ${Date.now()}`;
    let createdVideoId: string | undefined;

    try {
      await openTab(page, 'Video Analysis');
      await expect(page.getByRole('heading', { name: 'Video Analysis', level: 1 })).toBeVisible();

      await page.getByRole('button', { name: 'Add Video' }).click();
      const modal = page.locator('.fixed.inset-0').filter({ hasText: 'Add New Video' });
      await expect(modal).toContainText('Add New Video');
      await modal.getByLabel('Video URL').fill('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
      await modal.getByLabel('Title').fill(uniqueTitle);
      await modal.getByLabel('Player Name').fill('Playwright Scout');
      await modal.getByLabel('Match Details').fill('Playwright XI vs Regression United (2-1)');
      await modal.getByLabel('Tags').fill('playwright, regression');
      await modal.getByLabel('Description').fill('Browser-created regression video.');
      await page.getByRole('button', { name: 'Add Video' }).last().click();

      await expect(page.locator('main')).toContainText(uniqueTitle, { timeout: 15000 });
      await expect(page.locator('main')).toContainText('No annotations yet');

      const listResponse = await request.get('/api/v2/videos');
      expect(listResponse.ok()).toBeTruthy();
      const videos = await listResponse.json();
      const createdVideo = videos.find((video: any) => video.title === uniqueTitle);
      createdVideoId = createdVideo?.id || createdVideo?._id;
      expect(createdVideoId).toBeTruthy();

      await page.getByRole('button', { name: 'Add Note' }).click();
      const annotationModal = page.locator('.fixed.inset-0').filter({ hasText: 'Add Annotation' });
      await expect(annotationModal).toContainText('Add Annotation');
      await annotationModal.locator('textarea').fill(annotationText);
      await annotationModal.getByRole('button', { name: 'Add', exact: true }).click();

      await expect(page.locator('main')).toContainText(annotationText, { timeout: 15000 });
      await expect(page.locator('main')).toContainText('Annotations (1)', { timeout: 15000 });
    } finally {
      if (createdVideoId) {
        await request.delete(`/api/v2/videos/${createdVideoId}`);
      }
    }
  });
});

test.describe('remaining high-value tabs', () => {
  test.setTimeout(60000);

  test('advanced search and player comparison use live player data', async ({ page, request }) => {
    const players = await getPlayers(request, 4);
    expect(players.length).toBeGreaterThanOrEqual(2);

    const [firstPlayer, secondPlayer] = players;
    const searchQuery = firstPlayer.name.split(/\s+/)[0] || firstPlayer.name;

    await seedAuthenticatedSession(page, 'scout');
    await page.goto('/');

    await openTab(page, 'Advanced Search');
    await expect(page.getByRole('heading', { name: 'Advanced Search', level: 1 })).toBeVisible();

    const advancedSearchInput = page.getByPlaceholder('Search players, matches, teams, reports...');
    await advancedSearchInput.fill(searchQuery);

    const searchResultsDropdown = page.locator('.absolute.z-50').filter({ hasText: firstPlayer.name }).first();
    await expect(searchResultsDropdown).toBeVisible();
    await expect(searchResultsDropdown).toContainText(firstPlayer.name);
    expect(await searchResultsDropdown.getByRole('button').count()).toBeGreaterThan(0);

    await advancedSearchInput.press('Escape');
    await expect(searchResultsDropdown).toBeHidden();

    const filtersToggle = page.getByRole('button', { name: /^Filters$/ });
    await filtersToggle.click();
    await expect(page.locator('main')).toContainText('Apply Filters');
    await filtersToggle.click();
    await expect(page.locator('main')).not.toContainText('Apply Filters');

    await openTab(page, 'Player Comparison');
    await expect(page.getByRole('heading', { name: 'Player Comparison', level: 1 })).toBeVisible();

    await page.getByRole('button', { name: 'Select Players' }).click();
    const comparisonSearch = page.getByPlaceholder('Search players...');

    await comparisonSearch.fill(firstPlayer.name.split(/\s+/)[0] || firstPlayer.name);
    await page
      .getByRole('button', { name: new RegExp(escapeRegExp(firstPlayer.name)) })
      .first()
      .click();

    await comparisonSearch.fill(secondPlayer.name.split(/\s+/)[0] || secondPlayer.name);
    await page
      .getByRole('button', { name: new RegExp(escapeRegExp(secondPlayer.name)) })
      .first()
      .click();

    await expect(page.locator('main')).toContainText('Comparing 2 players across', { timeout: 15000 });
    await expect(page.locator('main')).toContainText('Profile');
    await expect(page.locator('main')).toContainText('Performance');

    await page.getByRole('button', { name: 'Refresh Comparison' }).click();
    await expect(page.locator('main')).toContainText('Distribution', { timeout: 15000 });
  });

  test('collaboration hub and calendar support create flows with cleanup', async ({ page, request }) => {
    const workspaceName = `Playwright Workspace ${Date.now()}`;
    const taskTitle = `Playwright Task ${Date.now()}`;
    const eventTitle = `Playwright Event ${Date.now()}`;
    const today = new Date().toISOString().slice(0, 10);

    await seedAuthenticatedSession(page, 'scout');
    await page.goto('/');

    try {
      await openTab(page, 'Collaboration Hub');
      await expect(page.getByRole('heading', { name: 'Collaboration Hub', level: 1 })).toBeVisible();

      await page.getByRole('button', { name: 'New Workspace' }).click();
      const workspaceModal = page.locator('.fixed.inset-0').filter({ hasText: 'Create New Workspace' });
      await workspaceModal.getByPlaceholder('e.g., Premier League Prospects').fill(workspaceName);
      await workspaceModal.getByPlaceholder('What is this workspace for?').fill('Automated workspace coverage for regression validation.');
      await workspaceModal.getByRole('button', { name: 'Create Workspace' }).click();

      await expect(page.locator('main')).toContainText(workspaceName, { timeout: 15000 });

      await page.getByRole('button', { name: 'Tasks' }).click();
      await page.getByRole('button', { name: 'New Task' }).click();
      const taskModal = page.locator('.fixed.inset-0').filter({ hasText: 'Create New Task' });
      await taskModal.getByPlaceholder('e.g., Scout Haaland in next match').fill(taskTitle);
      await taskModal.getByPlaceholder('What needs to be done?').fill('Automated task coverage for collaboration workflows.');
      await taskModal.locator('select').first().selectOption('high');
      await taskModal.getByRole('button', { name: 'Create Task' }).click();

      await expect(page.locator('main')).toContainText(taskTitle, { timeout: 15000 });

      await openTab(page, 'Calendar & Schedule');
      await expect(page.getByRole('heading', { name: 'Calendar & Scheduling', level: 1 })).toBeVisible();

      await page.getByRole('button', { name: 'New Event' }).click();
      const eventModal = page.locator('.fixed.inset-0').filter({ hasText: 'Create New Event' });
      await eventModal.getByPlaceholder('e.g., Man City vs Arsenal').fill(eventTitle);
      await eventModal.getByPlaceholder('Event details...').fill('Automated event coverage for calendar workflows.');
      await eventModal.locator('input[type="date"]').nth(0).fill(today);
      await eventModal.locator('input[type="time"]').nth(0).fill('10:00');
      await eventModal.locator('input[type="date"]').nth(1).fill(today);
      await eventModal.locator('input[type="time"]').nth(1).fill('11:00');
      await eventModal.getByPlaceholder('e.g., Etihad Stadium').fill('ScoutPro Training Ground');
      await eventModal.getByRole('button', { name: 'Create Event' }).click();

      await expect(page.locator('main')).toContainText(eventTitle, { timeout: 15000 });

      await page.getByRole('button', { name: 'Scouting Trips' }).click();
      await expect(page.locator('main')).toContainText(/Scouting Trips|No scouting trips found/);

      await page.getByRole('button', { name: 'Match Schedule' }).click();
      await expect(page.locator('main')).toContainText('Match Schedule');
    } finally {
      await deleteCollaborationEntities(request, workspaceName, taskTitle);
      await deleteCalendarEventByTitle(request, eventTitle);
    }
  });

  test('player profiles and scouting hub expose profile and scouting views', async ({ page }) => {
    await seedAuthenticatedSession(page, 'scout');
    await page.goto('/');

    await openTab(page, 'Player Profiles');
    await expect(page.getByRole('heading', { name: 'Player Database', level: 1 })).toBeVisible();

    await expect(page.locator('main')).toContainText(/Showing \d+ players/, { timeout: 15000 });
    await page.locator('main .grid img').first().click();

    await expect(page.getByRole('button', { name: 'Back to Players' })).toBeVisible();
    await expect(page.locator('main')).toContainText('Performance Metrics');
    await expect(page.locator('main')).toContainText('Market Value');
    await page.getByRole('button', { name: 'Back to Players' }).click();
    await expect(page.getByRole('heading', { name: 'Player Database', level: 1 })).toBeVisible();

    await openTab(page, 'Scouting Hub');
    await expect(page.getByRole('heading', { name: 'Scouting Dashboard', level: 1 })).toBeVisible();
    await expect(page.locator('main')).toContainText(/AI Recommendations|No AI recommendations available/);
    await expect(page.locator('main')).toContainText('Scouting Overview');
    await expect(page.locator('main')).toContainText('Search Results');

    const scoutingSelect = page.locator('main select').first();
    await scoutingSelect.selectOption('ST');
    await page.locator('main input[placeholder="Min age"]').fill('18');
    await page.locator('main input[placeholder="Max age"]').fill('24');
    await expect(page.locator('main')).toContainText(/players found|No players found/);
  });

  test('analytics lab and ml laboratory render live analytics and model catalog', async ({ page }) => {
    await seedAuthenticatedSession(page, 'admin');
    await page.goto('/');

    await openTab(page, 'Analytics Lab');
    await expect(page.getByText('Loading...')).toBeHidden({ timeout: 30000 });
    await expect(page.getByRole('heading', { name: 'Analytics Lab', level: 1 })).toBeVisible({ timeout: 30000 });
    await expect(page.locator('main')).toContainText('Team Style Clustering');
    await expect(page.locator('main')).toContainText('Expected Threat (xT) Analysis');

    const analyticsSelects = page.locator('main select');
    await analyticsSelects.first().selectOption('month');
    await analyticsSelects.nth(1).selectOption('xG');
    await expect(page.locator('main')).toContainText('Key Insight');

    await openTab(page, 'ML Laboratory');
    await expect(page.getByRole('heading', { name: 'ML Laboratory', level: 1 })).toBeVisible();
    await expect(page.locator('main')).toContainText('Algorithm Selection');
    await expect(page.locator('main')).toContainText('Dataset Selection');
    await expect(page.locator('main')).toContainText('Experiment History');
    await expect(page.locator('main')).toContainText('Start Training');

    await page.getByRole('button', { name: 'Refresh Catalog' }).click();
    await expect(page.locator('main')).toContainText(/Available Models|Loading algorithms.../);
    await expect(page.locator('main')).toContainText(/Datasets Online|Loading datasets.../);
  });

  test('data import export and transfer hub cover data operations and market tabs', async ({ page }) => {
    await seedAuthenticatedSession(page, 'admin');
    await page.goto('/');

    const importFileName = `playwright-import-${Date.now()}.csv`;

    await openTab(page, 'Data Import/Export');
    await expect(page.getByText('Loading...')).toBeHidden({ timeout: 30000 });
    await expect(page.getByRole('heading', { name: 'Data Import/Export', level: 1 })).toBeVisible({ timeout: 30000 });

    await page.locator('input[type="file"]').setInputFiles({
      name: importFileName,
      mimeType: 'text/csv',
      buffer: Buffer.from('name,position,club\nPlaywright Prospect,ST,ScoutPro FC\n'),
    });

    await expect(page.locator('main')).toContainText('Data Preview');
    await page.getByRole('button', { name: 'Start Import' }).click();
    await expect(page.locator('main')).toContainText(`Import job started for ${importFileName}.`, { timeout: 15000 });
    await expect(page.locator('main')).toContainText(importFileName, { timeout: 15000 });

    await page.getByRole('button', { name: 'Templates' }).click();
    await expect(page.locator('main')).toContainText(/Download Template|Loading import templates.../);

    await openTab(page, 'Transfer Hub');
    await expect(page.getByRole('heading', { name: 'Transfer Hub', level: 1 })).toBeVisible();
    await expect(page.locator('main')).toContainText('Market Trends by Position');

    await page.getByRole('button', { name: 'Transfer Rumors' }).click();
    await expect(page.locator('main')).toContainText('Transfer Rumors');

    await page.getByRole('button', { name: 'Valuations' }).click();
    await expect(page.locator('main')).toContainText(/AI Valuation Predictions|No valuation predictions available./);

    await page.getByRole('button', { name: 'Contract Expiry' }).click();
    await expect(page.locator('main')).toContainText(/Contract Expirations|No contract expiry data available./);
  });
});