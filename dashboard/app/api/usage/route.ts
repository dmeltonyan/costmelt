// Dashboard API Route - Usage

export async function GET(request: Request) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const { searchParams } = new URL(request.url);
  const days = searchParams.get('days') || '7';
  
  try {
    const response = await fetch(`${apiUrl}/dashboard/usage?days=${days}`, {
      cache: 'no-store',
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch usage');
    }
    
    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error('Error fetching usage:', error);
    return Response.json(
      { error: 'Failed to fetch usage' },
      { status: 500 }
    );
  }
}

