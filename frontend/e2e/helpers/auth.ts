import { Page } from '@playwright/test';

type TestRole = 'admin' | 'scout';

const rolePermissions: Record<TestRole, string[]> = {
  admin: [
    'view_players',
    'view_matches',
    'create_reports',
    'export_data',
    'manage_users',
    'manage_system',
    'manage_data',
    'delete_data',
    'view_analytics',
    'manage_roles',
  ],
  scout: [
    'view_players',
    'view_matches',
    'create_reports',
    'export_data',
    'video_analysis',
  ],
};

export async function seedAuthenticatedSession(page: Page, role: TestRole): Promise<void> {
  const email = role === 'admin' ? 'admin@scoutpro.dev' : 'demo@scoutpro.com';
  const now = new Date().toISOString();

  await page.addInitScript(
    ({ authRole, authEmail, permissions, timestamp }) => {
      localStorage.setItem('scoutpro_token', `playwright-${authRole}-token`);
      localStorage.setItem(
        'scoutpro_user',
        JSON.stringify({
          id: `playwright-${authRole}`,
          email: authEmail,
          name: authRole,
          role: authRole,
          team: 'ScoutPro Test Club',
          permissions,
          createdAt: timestamp,
          updatedAt: timestamp,
        })
      );
    },
    {
      authRole: role,
      authEmail: email,
      permissions: rolePermissions[role],
      timestamp: now,
    }
  );
}

export async function openTab(page: Page, label: string): Promise<void> {
  await page.locator(`button:has-text("${label}")`).first().evaluate((node) => {
    (node as HTMLButtonElement).click();
  });
}