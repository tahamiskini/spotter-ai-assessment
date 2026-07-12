export const paths = {
  home: {
    path: '/',
    getHref: () => '/',
  },
  trip: {
    path: 'trips/:tripId',
    getHref: (tripId: string) => `/trips/${tripId}`,
  },
} as const;
