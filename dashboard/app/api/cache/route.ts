// Dashboard API Route - Cache Stats

export async function GET() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  try {
    const response = await fetch(`${apiUrl}/dashboard/cache`, {
      cache: 'no-store',
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch cache stats');
    }
    
    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error('Error fetching cache stats:', error);
    return Response.json(
      { error: 'Failed to fetch cache stats' },
      { status: 500 }
    );
  }
}

