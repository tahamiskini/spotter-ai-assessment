import {
  render as rtlRender,
  screen,
  waitForElementToBeRemoved,
} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RouterProvider, createMemoryRouter } from 'react-router';

import { AppProvider } from '@/app/provider';

export const waitForLoadingToFinish = () =>
  waitForElementToBeRemoved(
    () => [
      ...screen.queryAllByTestId(/loading/i),
      ...screen.queryAllByText(/loading/i),
    ],
    { timeout: 4000 },
  );

/** Render a component inside the app providers + a memory router. */
export const renderApp = (
  ui: React.ReactNode,
  { url = '/', path = '/', ...renderOptions }: Record<string, any> = {},
) => {
  const router = createMemoryRouter([{ path, element: ui }], {
    initialEntries: [url],
  });

  return rtlRender(
    <AppProvider>
      <RouterProvider router={router} />
    </AppProvider>,
    renderOptions,
  );
};

export * from '@testing-library/react';
export { userEvent, rtlRender };
