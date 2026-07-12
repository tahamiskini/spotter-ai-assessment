import { useParams } from 'react-router';

import { ContentLayout } from '@/components/layouts';
import { Link } from '@/components/ui/link';
import { Spinner } from '@/components/ui/spinner';
import { paths } from '@/config/paths';
import { useTrip } from '@/features/trips/api/get-trip';
import { TripPlanner } from '@/features/trips/components/trip-planner';

const TripRoute = () => {
  const { tripId } = useParams();
  const tripQuery = useTrip({ tripId: tripId as string });

  if (tripQuery.isLoading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  const trip = tripQuery.data;

  if (!trip) {
    return (
      <ContentLayout title="Trip not found">
        <p className="text-sm text-muted-foreground">
          We couldn&apos;t load this trip.{' '}
          <Link to={paths.home.getHref()}>Plan a new one</Link>.
        </p>
      </ContentLayout>
    );
  }

  return (
    <ContentLayout title="Trip plan">
      <TripPlanner initialTrip={trip} />
    </ContentLayout>
  );
};

export default TripRoute;
