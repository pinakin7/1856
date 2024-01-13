from matplotlib import pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

urls = {
    "shortterm": "https://markets.businessinsider.com/bonds/finder?{}borrower=71&maturity=shortterm&yield=&bondtype=2"
                 "%2c3%2c4%2c16&coupon=&currency=184&rating=&country=19",
    "midterm": "https://markets.businessinsider.com/bonds/finder?{}borrower=71&maturity=midterm&yield=&bondtype=2"
               "%2c3%2c4%2c16&coupon=&currency=184&rating=&country=19"
}

base_url = "https://markets.businessinsider.com"

def plot_coupon_issue(df):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Colormap normalization
    norm = Normalize(vmin=df['Bond Years'].min(), vmax=df['Bond Years'].max())
    sm = ScalarMappable(cmap='viridis', norm=norm)
    sm.set_array([])

    scatter = ax.scatter(df['Issue Year'], df['Coupon'], marker='o',
                         label='Coupon Percent (Issue)', c=df['Bond Years'], cmap='viridis')

    cbar = plt.colorbar(sm, ax=ax, label='Bond Years')
    ax.set_xlabel('Issue Date')
    ax.set_ylabel('Coupon %')
    ax.set_title('Coupon % vs. Issue Year (Colored by Bond Years)')
    ax.grid(True)
    plt.show()