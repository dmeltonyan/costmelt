// Dashboard API Route - Daily Stats

export async function GET(request: Request) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const { searchParams } = new URL(request.url);
  const days = searchParams.get('days') || '30';
  
  try {
    const response = await fetch(`${apiUrl}/dashboard/daily?days=${days}`, {
      cache: 'no-store',
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch daily stats');
    }
    
    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error('Error fetching daily stats:', error);
    return Response.json(
      { error: 'Failed to fetch daily stats' },
      { status: 500 }
    );
  }
}

