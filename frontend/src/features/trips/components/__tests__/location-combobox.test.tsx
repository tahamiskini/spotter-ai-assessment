import { useState } from 'react';

import {
  renderApp,
  screen,
  userEvent,
  waitFor,
} from '@/testing/test-utils';

import { LocationCombobox } from '../location-combobox';

const Harness = () => {
  const [value, setValue] = useState('');
  return (
    <div>
      <LocationCombobox label="Current location" value={value} onChange={setValue} />
      <output data-testid="value">{value}</output>
    </div>
  );
};

describe('LocationCombobox', () => {
  it('shows geocode suggestions while typing and fills the value on select', async () => {
    await renderApp(<Harness />);

    const input = screen.getByRole('combobox');
    await userEvent.type(input, 'phoe');

    // Suggestion comes from the mocked /geocode endpoint.
    const option = await screen.findByRole('option', { name: /phoenix/i }, {
      timeout: 3000,
    });
    await userEvent.click(option);

    await waitFor(() =>
      expect(screen.getByTestId('value')).toHaveTextContent('Phoenix'),
    );
    expect(input).toHaveValue('Phoenix');
  });

  it('keeps a free-typed value that matches no suggestion', async () => {
    await renderApp(<Harness />);

    const input = screen.getByRole('combobox');
    await userEvent.type(input, 'Nowheresville, ZZ');

    expect(screen.getByTestId('value')).toHaveTextContent('Nowheresville, ZZ');
  });
});
