// Dashboard API Route - Stats

export async function GET() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  try {
    const response = await fetch(`${apiUrl}/dashboard/stats`, {
      cache: 'no-store',
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch stats');
    }
    
    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error('Error fetching stats:', error);
    return Response.json(
      { error: 'Failed to fetch stats' },
      { status: 500 }
    );
  }
}

