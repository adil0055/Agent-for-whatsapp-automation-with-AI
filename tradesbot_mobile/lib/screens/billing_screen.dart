import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:lucide_icons/lucide_icons.dart';

class BillingScreen extends StatelessWidget {
  const BillingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        bottom: false,
        child: CustomScrollView(
          slivers: [
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(24, 40, 24, 30),
              sliver: SliverToBoxAdapter(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Credits & Billing',
                      style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 36),
                    ).animate().fade(duration: 400.ms).slideY(begin: -0.2),
                    const SizedBox(height: 12),
                    Text(
                      'Manage your AI assistant balance and view billing history.',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontSize: 16, height: 1.5),
                    ).animate().fade(delay: 100.ms, duration: 400.ms),
                  ],
                ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              sliver: SliverToBoxAdapter(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildBalanceCard().animate().fade(delay: 200.ms).scale(begin: const Offset(0.95, 0.95)),
                    const SizedBox(height: 40),
                    Text(
                      'Top Up (Test Payment)',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(fontSize: 20),
                    ).animate().fade(delay: 300.ms),
                    const SizedBox(height: 20),
                    _buildTopUpOption(
                      credits: '100 Credits',
                      price: '\$20.00',
                      delay: 400,
                      context: context,
                    ),
                    const SizedBox(height: 16),
                    _buildTopUpOption(
                      credits: '500 Credits',
                      price: '\$85.00',
                      delay: 500,
                      isPopular: true,
                      context: context,
                    ),
                    const SizedBox(height: 140), // Padding for bottom nav
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBalanceCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF231E05), Color(0xFF141203)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(32),
        border: Border.all(color: const Color(0xFFFFD700).withOpacity(0.15)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFFFFD700).withOpacity(0.05),
            blurRadius: 30,
            offset: const Offset(0, 10),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(LucideIcons.zap, color: Color(0xFFFFD700), size: 20),
              const SizedBox(width: 10),
              Text(
                'AVAILABLE CREDITS',
                style: TextStyle(
                  color: const Color(0xFFFFD700).withOpacity(0.9),
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          const Text(
            '42',
            style: TextStyle(
              color: Colors.white,
              fontSize: 64,
              fontWeight: FontWeight.w700,
              height: 1,
              letterSpacing: -2,
            ),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: const BoxDecoration(
                  color: Color(0xFF10B981),
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 10),
              const Text(
                'AI Assistant is Active',
                style: TextStyle(
                  color: Color(0xFFB0B3BC),
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTopUpOption({
    required String credits,
    required String price,
    required int delay,
    required BuildContext context,
    bool isPopular = false,
  }) {
    return GestureDetector(
      onTap: () {
        _showTestPaymentDialog(context, price, credits);
      },
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF14151C),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: isPopular ? const Color(0xFFFFD700) : Colors.white.withOpacity(0.05),
            width: isPopular ? 1.5 : 1,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      credits,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.w600,
                        letterSpacing: -0.3,
                      ),
                    ),
                    if (isPopular) ...[
                      const SizedBox(width: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFD700).withOpacity(0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text(
                          'POPULAR',
                          style: TextStyle(
                            color: Color(0xFFFFD700),
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1.2,
                          ),
                        ),
                      ),
                    ]
                  ],
                ),
                const SizedBox(height: 6),
                const Text(
                  'One-time top up',
                  style: TextStyle(
                    color: Color(0xFF8A8F9E),
                    fontSize: 14,
                  ),
                ),
              ],
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              decoration: BoxDecoration(
                color: isPopular ? const Color(0xFFFFD700) : const Color(0xFF262A36),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                price,
                style: TextStyle(
                  color: isPopular ? Colors.black : Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 16,
                ),
              ),
            ),
          ],
        ),
      ).animate().fade(delay: delay.ms).slideY(begin: 0.1),
    );
  }

  void _showTestPaymentDialog(BuildContext context, String price, String credits) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => Container(
        padding: const EdgeInsets.all(32),
        decoration: const BoxDecoration(
          color: Color(0xFF14151C),
          borderRadius: BorderRadius.vertical(top: Radius.circular(40)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 48,
                height: 6,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(3),
                ),
              ),
            ),
            const SizedBox(height: 40),
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: const Color(0xFFFFD700).withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Center(
                child: Icon(LucideIcons.shieldCheck, color: Color(0xFFFFD700), size: 40),
              ),
            ),
            const SizedBox(height: 32),
            Text(
              'Test Payment Mode',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 28),
            ),
            const SizedBox(height: 12),
            Text(
              'This simulates adding $credits to your account for $price. No real charge will be made.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontSize: 16, height: 1.5),
            ),
            const SizedBox(height: 40),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: const Text('Test Payment Successful! Credits added.'),
                    backgroundColor: const Color(0xFF10B981),
                    behavior: SnackBarBehavior.floating,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFFD700),
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(vertical: 20),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                elevation: 0,
              ),
              child: const Text(
                'Complete Mock Payment',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -0.2,
                ),
              ),
            ),
            const SizedBox(height: 20),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text(
                'Cancel',
                style: TextStyle(color: Color(0xFF8A8F9E), fontSize: 16, fontWeight: FontWeight.w600),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
