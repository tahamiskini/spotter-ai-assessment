import { ContentLayout } from '@/components/layouts';
import { TripPlanner } from '@/features/trips/components/trip-planner';

const HomeRoute = () => {
  return (
    <ContentLayout title="Plan a trip">
      <TripPlanner />
    </ContentLayout>
  );
};

export default HomeRoute;
